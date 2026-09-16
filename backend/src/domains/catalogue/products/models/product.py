"""
Product -- the SHARED, PLATFORM-OWNED thing itself, as opposed to any
one supplier's offer of it.

"Coca-Cola Original 2L" is one row here no matter how many suppliers
sell it. That is the entire point: without it, two suppliers' rows for
the same physical product have no relationship to each other, and "who
sells this cheaper" is unanswerable by construction rather than merely
hard (V2_00 section 2.1).

THIS ARRIVES DORMANT, AND THAT IS THE DESIGN. Nothing reads this table
yet. SupplierOffer.product_id is NULLABLE, so an unmatched offer behaves
exactly as it did before this step existed -- the catalogue can sit
empty for as long as it takes, and matching fills it in over time
without a flag day. Shipping a schema that nothing depends on is what
turns a rewrite into a migration.

THE PRODUCT IS THE CONSUMER UNIT. "Coca-Cola Original 2L" -- one
bottle, the thing with the barcode on it. How many are in a case is NOT
recorded here; it lives on the offer, because it is that supplier's
packing decision. Put pack size here instead and a supplier selling
6-packs never compares against one selling 12-packs, though the buyer
simply wants the product cheaply. Decided 2026-09-08, V2_00 section 2.1.

The cost of that decision, stated plainly: case barcodes (GTIN-14) no
longer map one-to-one onto products. A scanned case code resolves
through the OFFER; a consumer code resolves through this table. One
piece of special-casing, in one place, traded for comparison working
everywhere.

IMAGES ARE AN ENRICHMENT, NEVER A GATE. image_url is nullable and
expected to be null for most rows for a long time. A product exists the
moment it has a name, a brand and a pack; a tile that has no image for
it falls through to the brand mark and then the category image and never
renders blank (V2_00 section 2.8). If the catalogue could not launch
without images, image sourcing would block the whole architecture -- and
it must not.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.domains.catalogue.products.models.taxonomy import (
    TAXONOMY_TYPE_SCHEMA,
    ProductCategory,
    ProductUnit,
)
from src.extensions import db


class Product(BaseModel):
    __tablename__ = "products"
    __table_args__ = (
        db.Index("ix_catalogue_products_normalized_name", "normalized_name"),
        db.Index("ix_catalogue_products_brand_id", "brand_id"),
        # GTIN is the one identifier that is unambiguous, so it is the
        # first thing matching tries and the only match that needs no
        # model call at all. UNIQUE because two catalogue rows sharing a
        # barcode means the catalogue is already wrong.
        db.UniqueConstraint("gtin", name="uq_catalogue_products_gtin"),
        {"schema": "catalogue"},
    )

    #: As a human would write it: "Coca-Cola Original 2L".
    name = db.Column(db.String(200), nullable=False)

    #: The matching key -- lowercased, punctuation stripped, spacing
    #: collapsed. Indexed because candidate search runs against it for
    #: every row of every import, and a supplier's file has thousands.
    normalized_name = db.Column(db.String(200), nullable=False)

    #: NULLABLE, because unbranded goods are real -- loose potatoes, a
    #: bag of sand. Not every product has a brand and pretending
    #: otherwise would force junk rows into the brand table.
    brand_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("catalogue.brands.id"), nullable=True
    )

    #: A fact about the product, not about anyone's offer of it -- which
    #: is why the taxonomy moved to this domain in this same step. The
    #: Postgres TYPE still lives in the supplier schema; see taxonomy.py
    #: for why that is deliberate and not an oversight.
    category = db.Column(
        db.Enum(ProductCategory, name="product_category", schema=TAXONOMY_TYPE_SCHEMA),
        nullable=False,
    )

    #: The CONSUMER unit: 2 / L for a 2L bottle. Nullable together --
    #: a product sold simply "each" needs neither.
    unit_quantity = db.Column(db.Integer, nullable=True)
    unit_measure = db.Column(
        db.Enum(ProductUnit, name="product_unit", schema=TAXONOMY_TYPE_SCHEMA),
        nullable=True,
    )

    #: HOW MANY CONSUMER UNITS ARE IN THE PACK: 24 for "Doritos 36g x24",
    #: 6 for "COKE 2LT PET 6PK". NULL means a single, which is the
    #: overwhelming majority and the reason this is not defaulted to 1 --
    #: "nobody said" and "explicitly one" are the same product, but only
    #: one of them is a fact somebody stated.
    #:
    #: IT WAS EXTRACTED AND THEN DISCARDED FOR MONTHS. pack_size.py has
    #: always read "x24" correctly and PackSize has always carried it;
    #: there was simply nowhere to put it, so _create_and_link dropped it
    #: on the way in and _pack_agreement had nothing to compare. The
    #: consequence was measurable on the seeded catalogue: ONE product
    #: holding a single 36g bag of Doritos at R6.00 and a case of 24 at
    #: R139.50, offered to shopkeepers as alternatives to each other,
    #: because they agree on every fact the catalogue stored -- same
    #: brand, same 36g consumer unit.
    #:
    #: A DIFFERING COUNT IS A DISAGREEMENT, and carries the same -0.40 as
    #: a differing size (confidence.score_rules_match). The reason is the
    #: same too: "Doritos 36g" and "Doritos 36g x24" are nearly identical
    #: as text and are not the same purchase, and getting it wrong puts a
    #: per-unit price on a card that is out by a factor of twenty-four.
    pack_quantity = db.Column(db.Integer, nullable=True)

    #: The consumer-unit barcode. NULLABLE: plenty of real products have
    #: no barcode we know, and refusing to catalogue them would make the
    #: catalogue useless for exactly the informal-trade goods this
    #: platform exists to serve. String, never an integer -- leading
    #: zeros are significant in a GTIN.
    gtin = db.Column(db.String(14), nullable=True)

    #: Tier 1 of the image cascade. Null is the normal state.
    image_url = db.Column(db.String(500), nullable=True)
