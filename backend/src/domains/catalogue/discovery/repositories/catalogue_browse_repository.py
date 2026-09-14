"""
Browsing the catalogue across every supplier.

THE QUERY THAT DID NOT EXIST. Every product read in this codebase is
scoped to ONE supplier's shopfront -- catalog_service,
list_profile_products, previously_ordered_product_ids. Nothing could
answer "what drinks can I buy, from anyone", which is why tapping a
category chip routed to SUPPLIER search and found shops instead of
stock.

IT BROWSES OFFERS, GROUPED BY CATALOGUE PRODUCT -- NOT THE CATALOGUE.
That is a deliberate inversion of what docs/v2/V2_15 Book Two proposed,
and the data is the reason: on 2026-09-14 there were 28 supplier offers,
ZERO of them matched, and ZERO catalogue products. A catalogue-first
browse would have returned an empty screen and looked like a bug.

So the catalogue is what makes the result BETTER, never what makes it
POSSIBLE:

    matching worked   three suppliers' "WHT SUGR 2.5KG", "White Sugar
                      2.5kg" and "Sugar White 2.5KG" collapse to ONE
                      card, and the shop picks a supplier rather than
                      squinting at three spellings
    matching has not  each offer stands alone. Honest, and exactly what
                      a shop would see on a shelf anyway

As match coverage rises the same screen quietly improves, with no
change here. That is the property worth having.

THE CURTAIN APPLIES, in SQL rather than afterwards -- a LIMIT in front
of an in-Python filter returns fewer rows than asked for, which is the
hazard visibility.py's own docstring warns about.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.extensions import db

#: How many offers to pull per requested card.
#:
#: GROUPING HAPPENS AFTER THE QUERY, so asking the database for exactly
#: `limit` offers would return fewer than `limit` CARDS whenever any two
#: of them are the same product. Four is generous for a market where a
#: product is carried by a handful of suppliers, and it is bounded --
#: never "fetch everything and sort in Python".
_OVERFETCH = 4


def browse(
    *,
    category: Optional[str] = None,
    categories: Optional[List[str]] = None,
    search: Optional[str] = None,
    limit: int = 24,
    offset: int = 0,
) -> List[List]:
    """Live offers from visible suppliers, grouped into one list per
    catalogue product.

    Returns a list of GROUPS, each a list of SupplierOffer rows for the
    same product, so the caller decides which to show (offer_selection)
    rather than this deciding for them. A repository that picked would
    be making a product decision in a place nobody looks for one.

    Ordering is by name, deliberately boring: relevance ranking belongs
    to the feed, and a category browse that reorders itself between
    visits is one a shopkeeper cannot learn.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
    from src.domains.verification.visibility import visible_filter

    query = (
        db.session.query(SupplierOffer)
        .join(SupplierProfile, SupplierProfile.id == SupplierOffer.supplier_profile_id)
        .filter(
            visible_filter(),
            SupplierOffer.is_deleted.is_(False),
            SupplierOffer.is_archived.is_(False),
        )
    )

    # SEVERAL CATEGORIES IN ONE QUERY, because the demand engine asks
    # for everything a shop buys at once. Looping a single-category
    # browse would be one query per declared category -- the N+1 this
    # codebase has removed three times now, arriving by a new route.
    if categories:
        query = query.filter(SupplierOffer.category.in_(categories))
    elif category:
        query = query.filter(SupplierOffer.category == category)

    if search:
        # ILIKE with the wildcards escaped -- a shopper typing "50%"
        # should search for "50%", not match everything. Same treatment
        # as the supplier search (test_like_escaping.py exists because
        # this was got wrong once already).
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.filter(SupplierOffer.name.ilike(f"%{escaped}%", escape="\\"))

    rows = (
        query.order_by(SupplierOffer.name.asc())
        .offset(offset)
        .limit(limit * _OVERFETCH)
        .all()
    )

    return _group_by_product(rows, limit)


def _group_by_product(offers: List, limit: int) -> List[List]:
    """One group per catalogue product; an UNMATCHED offer is its own
    group.

    KEYED ON THE OFFER'S OWN ID WHEN product_id IS NULL, never on the
    name. Two suppliers spelling the same thing differently are not
    known to be the same thing -- that is precisely the judgement the
    matching ladder makes with a confidence score and a review queue,
    and guessing it here with a string comparison would be that whole
    system done badly in one line.
    """
    groups: dict = {}
    order: List = []

    for offer in offers:
        key = offer.product_id or ("offer", offer.id)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(offer)

    return [groups[key] for key in order[:limit]]


def count_for_category(category: str) -> int:
    """How many live offers a category actually has.

    Used to decide whether a chip is worth showing at all: a category
    chip that leads to an empty screen is worse than one that is absent,
    and it is the first thing a new user taps.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
    from src.domains.verification.visibility import visible_filter

    return (
        db.session.query(SupplierOffer.id)
        .join(SupplierProfile, SupplierProfile.id == SupplierOffer.supplier_profile_id)
        .filter(
            visible_filter(),
            SupplierOffer.is_deleted.is_(False),
            SupplierOffer.is_archived.is_(False),
            SupplierOffer.category == category,
        )
        .count()
    )
