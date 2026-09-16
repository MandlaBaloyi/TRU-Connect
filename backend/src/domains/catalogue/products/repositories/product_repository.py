"""
Catalogue product lookups. Pure SQL, no business rules -- same rule as
every other repository here.

THE THREE READS ARE THE THREE FREE TIERS. get_by_gtin is tier 0,
get_by_matching_key is tier 2, and search_similar is tier 3. Tier 1
(aliases) lives in the matching domain because it is learned rather than
inherent.

SIMILARITY IS COMPUTED IN POSTGRES, NOT PYTHON, and that is not an
optimisation -- it is the only version that works. A supplier file has
thousands of rows and the catalogue will have tens of thousands of
products; pulling every product into Python to score it is a
cross-product that gets slower with every supplier who joins. pg_trgm's
GIN index turns each lookup into an index scan.

It is also the same lesson the storefront ranking already records:
ranking in Python breaks the moment the query paginates.
"""
from __future__ import annotations

from typing import List, Optional, Tuple
from uuid import UUID

from src.domains.catalogue.products.models.product import Product
from src.extensions import db


class CatalogueProductRepository:
    @staticmethod
    def get_by_id(product_id: str | UUID) -> Optional[Product]:
        return Product.query.filter_by(id=product_id, is_deleted=False).first()

    # --- tier 0 ------------------------------------------------------------

    @staticmethod
    def get_by_gtin(gtin: str) -> Optional[Product]:
        """The only lookup that is certain. A GTIN identifies exactly one
        product, and the unique constraint on the column is what keeps
        that true."""
        if not gtin:
            return None
        return Product.query.filter_by(gtin=gtin.strip(), is_deleted=False).first()

    # --- tier 2 ------------------------------------------------------------

    @staticmethod
    def get_by_matching_key(key: str) -> Optional[Product]:
        """Same words, any order.

        Product does not store the sorted key -- it stores
        normalized_name -- so this compares against a key computed from
        that on the fly. Cheap because the candidate set is already
        narrow by the time this runs, and it avoids a second stored
        column that could drift out of step with the first.
        """
        if not key:
            return None

        from src.domains.catalogue.matching.algorithms.normalise import matching_key

        # Products whose normalised name is the same LENGTH -- a cheap
        # pre-filter so this is not a full scan. Sorting tokens cannot
        # change how many characters there are, so a product whose name
        # differs in length cannot possibly produce this key.
        #
        # COMPARED AGAINST THE WHOLE NAME, SPACES INCLUDED, because
        # matching_key joins its sorted tokens with "|" -- one separator
        # for each space the name had. Space-for-separator is
        # length-preserving, so the two are directly comparable.
        #
        # THIS LINE USED TO STRIP THE SPACES, matching a key that was
        # joined with nothing. When the separator was introduced -- so
        # that "bread"+"roll" could never collide with "breadroll" --
        # this filter silently stopped matching anything, and tier 2
        # went dark: every exact match quietly demoted to tier 3's fuzzy
        # scoring. Nothing failed, the right product was still usually
        # found, and the only visible symptom was a tier name in an
        # evidence blob. Caught by test_word_order_alone_does_not_
        # prevent_a_match, which asserts the TIER and not just the
        # answer -- which is exactly why it asserts the tier.
        candidates = Product.query.filter(
            Product.is_deleted.is_(False),
            db.func.length(Product.normalized_name) == len(key),
        ).all()
        for candidate in candidates:
            if matching_key(candidate.normalized_name) == key:
                return candidate
        return None

    # --- tier 3 ------------------------------------------------------------

    @staticmethod
    def search_similar(
        normalised_text: str, *, limit: int = 5, minimum: float = 0.3
    ) -> List[Tuple[Product, float]]:
        """The closest catalogue products by trigram similarity, best
        first, each with its score.

        RETURNS THE SCORE, not just the rows. The caller has to weigh it
        against brand and pack agreement before deciding anything, and a
        repository that threw the number away would force the service to
        recompute it in Python -- the exact thing this method exists to
        avoid.

        `minimum` is applied in SQL so genuinely unrelated products never
        leave the database.
        """
        if not normalised_text:
            return []

        # EVERYTHING FROM pg_trgm IS SCHEMA-QUALIFIED, and it has to be.
        # This database has no `public` schema, so the extension was
        # installed into `catalogue` (see migration c32c5e454643) and
        # nothing from it is on anyone's search_path. A bare
        # similarity() resolves to no function at all.
        similarity = db.func.catalogue.similarity(Product.normalized_name, normalised_text)

        # TWO FILTERS DOING DIFFERENT JOBS. The `%` operator is what the
        # GIN index can actually answer, so it narrows the scan; the
        # explicit >= then enforces the caller's own threshold, which
        # `%` cannot because it reads a session-wide setting rather than
        # an argument. Without the operator this is a sequential scan
        # that gets slower with every product ever added.
        indexed_narrow = db.text(
            "catalogue.products.normalized_name OPERATOR(catalogue.%) :trgm_query"
        ).bindparams(trgm_query=normalised_text)

        rows = (
            db.session.query(Product, similarity.label("score"))
            .filter(Product.is_deleted.is_(False), indexed_narrow, similarity >= minimum)
            .order_by(similarity.desc())
            .limit(limit)
            .all()
        )
        return [(product, float(score)) for product, score in rows]

    # --- writes ------------------------------------------------------------

    @staticmethod
    def create(**fields) -> Product:
        product = Product(**fields)
        db.session.add(product)
        db.session.flush()
        return product
