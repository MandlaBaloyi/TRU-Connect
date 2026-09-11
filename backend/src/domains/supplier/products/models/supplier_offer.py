"""
SupplierOffer -- ONE SUPPLIER'S OFFER OF ONE PRODUCT: their price, their
pack, their SKU, their stock.

RENAMED FROM `Product` IN V2 (see docs/v2/V2_00_ARCHITECTURE_EVOLUTION,
section 2.1). It was always this: the row carries supplier_profile_id,
price_cents, sku and is_archived, none of which are properties of a
product in the world -- they are properties of one supplier's offer of
it. V1 built the right table and gave it the wrong name, and the wrong
name is what made "who sells this cheaper" unaskable: two suppliers'
rows for the same physical thing had no relationship to each other.

THE LINK TO THE CATALOGUE IS NULLABLE, and that is the whole trick.
product_id points at catalogue.products, and an offer with it unset
behaves exactly as this row did before the catalogue existed. So the
catalogue could ship empty, nothing broke on the day it landed, and
matching fills the column in over time with no flag day.

PACK SIZE STAYS HERE, on the offer, not on that future Product
(V2_00 2.1, decided 2026-09-08). The catalogue Product is the CONSUMER
unit -- "Coca-Cola Original 2L". How many of them are in a case is this
supplier's decision, so unit_quantity/unit_measure and selling_unit
belong to the offer. Put pack size on the Product instead and a supplier
selling 6-packs never compares against one selling 12-packs, which
defeats the entire point of having a catalogue.

THE API STILL SAYS "products", DELIBERATELY. Routes
(/api/v1/supplier-discovery/products), JSON keys, schemas and the domain
folder are unchanged -- the mobile app is a shipped client and this
rename is internal. The contract moves when the catalogue makes it mean
something different, not before.

The rest of this file is as it was:

name, category, price, selling unit, the unit_quantity/unit_measure pair
("1 Case = 24 Bottles" math), and archive state -- matching the
frontend's own already-locked contract
(frontend/src/features/dashboard/supplier/products/types.ts) exactly,
field for field. Images are NOT a column here -- see ProductMedia
(added in the Media phase), a real FK'd table, not a JSON blob on this
row.

NO stock_status COLUMN -- deliberately absent, not an oversight. The
frontend already migrated stock status to be Inventory-derived
(computed from real quantity), not a value a supplier manually sets on
a product. Building a stock_status column here would mean building a
second, competing source of truth for something the frontend has
already settled -- see the Inventory domain's own ownership of that
concept.

Deliberately in the `supplier` schema (supplier.supplier_offers),
matching supplier.supplier_profiles' own placement. The future catalogue
Product will NOT live here -- it belongs to the platform, not to any
supplier, and gets its own schema.
"""
from __future__ import annotations


from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


# ProductCategory and ProductUnit MOVED to the catalogue domain in v2
# step 2 -- a category is a fact about a product, not about one
# supplier's offer of it. Re-exported here because this module's own
# columns use them and because a dozen call sites already import them
# from this path; the re-export keeps that working while the single
# definition lives where it belongs.
# The catalogue models this row points at are imported by
# create_app's _register_apiless_models(), not here -- see that
# function for why an API-less domain needs explicit registration.
from src.domains.catalogue.products.models.taxonomy import (  # noqa: F401
    TAXONOMY_TYPE_SCHEMA,
    ProductCategory,
    ProductUnit,
)


class SupplierOffer(BaseModel):
    __tablename__ = "supplier_offers"
    # THE INDEX AND CONSTRAINT NAMES ARE RENAMED TOO, and the migration
    # renames them in the database to match. Postgres does NOT rename
    # indexes or constraints when a table is renamed -- ALTER TABLE
    # RENAME touches only the table -- so leaving these as ix_products_*
    # here would have been the safe-looking option and the wrong one:
    # the names in metadata and the names in the database would agree
    # only by accident, and every future autogenerate would try to
    # "fix" it.
    #
    # Worth being explicit about because THE TEST SUITE CANNOT CATCH A
    # MISTAKE HERE. conftest builds the schema with db.create_all() from
    # this metadata and never runs a migration, so tests would pass
    # against a database no migration ever produces. This exact trap
    # already bit once (a hand-written migration that omitted
    # deleted_at). The dev database is checked directly instead.
    __table_args__ = (
        db.Index("ix_supplier_offers_supplier_profile_id", "supplier_profile_id"),
        # Matches the Products list screen's own real query shape
        # (supplier's own offers, excluding archived, newest first) --
        # named explicitly rather than left for the query planner to
        # discover under load.
        db.Index(
            "ix_supplier_offers_supplier_profile_id_is_archived",
            "supplier_profile_id",
            "is_archived",
        ),
        # product_code is PLATFORM-WIDE unique -- it's the short,
        # human-readable stand-in for this row's own UUID, shown to
        # both the supplier and any business ordering from them (see
        # algorithms/product_code_generator.py's own docstring).
        db.UniqueConstraint("product_code", name="uq_supplier_offers_product_code"),
        # sku is unique per SUPPLIER, not platform-wide -- matches how
        # SKUs actually work in the real world; every business has its
        # own numbering, with no expectation two unrelated suppliers
        # never reuse the same label (see algorithms/sku_generator.py's
        # own docstring).
        db.UniqueConstraint(
            "supplier_profile_id", "sku", name="uq_supplier_offers_supplier_profile_id_sku"
        ),
        {"schema": "supplier"},
    )

    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    # THE CATALOGUE LINK. Nullable, and null is a perfectly good state:
    # an unmatched offer is a normal offer, it simply cannot be compared
    # against another supplier's yet. Matching sets this later, gated on
    # confidence -- a WRONG match is worse than no match, because it
    # makes the price comparison a lie about two different things
    # (V2_00 section 2.7).
    #
    # ondelete is deliberately NOT cascade. Removing a catalogue product
    # must never delete a supplier's offer and the order history hanging
    # off it; the correct outcome is the offer falling back to unmatched.
    product_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("catalogue.products.id", ondelete="SET NULL"),
        nullable=True,
    )
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(
        db.Enum(ProductCategory, name="product_category", schema="supplier"), nullable=False
    )
    # BIGINT cents, never NUMERIC/DECIMAL/FLOAT -- same money convention
    # as loan_book/order_book's own amount columns throughout this
    # codebase.
    price_cents = db.Column(db.BigInteger, nullable=False)
    # The "was RX, now RY" comparison price -- optional; a supplier
    # running a sale/promotion sets this to what the item used to cost.
    # ALWAYS validated (services/product_service.py) to be strictly
    # greater than price_cents when provided -- a "discount" that's
    # actually a markup is either a mistake or meaningless, caught at
    # save time rather than silently published.
    compare_at_price_cents = db.Column(db.BigInteger, nullable=True)
    selling_unit = db.Column(
        db.Enum(ProductUnit, name="product_unit", schema="supplier"), nullable=False
    )
    # Schema-ready, not yet surfaced in any UI form -- see the
    # frontend's own Product.unitQuantity/unitMeasure docstring for the
    # full "1 Case = 24 Bottles" reasoning. Both nullable: a plain
    # "sold each" product never needs them populated.
    unit_quantity = db.Column(db.Integer, nullable=True)
    unit_measure = db.Column(
        db.Enum(ProductUnit, name="product_unit", schema="supplier"), nullable=True
    )
    is_archived = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())

    # Plain text -- "3 loaves per case", ingredients, anything a
    # supplier wants a business to see before ordering. Optional,
    # never required.
    description = db.Column(db.String(1000), nullable=True)

    # NEVER NULL, NEVER SUPPLIED BY A REQUEST -- both always generated
    # server-side before a row is ever inserted (see
    # services/product_service.py's own create_product). sku is
    # optional TO TYPE (auto-filled via algorithms/sku_generator.py
    # when left blank, still always ends up with a real value here);
    # product_code is NEVER typed by anyone, always
    # algorithms/product_code_generator.py's own output, and is never
    # editable once set.
    #: A HASH OF WHAT MATCHING LAST SAW -- name, barcode, brand and pack.
    #: Not the match result; the INPUTS that produced it.
    #:
    #: WHY THIS EXISTS. A real supplier sends a price file every week and
    #: only the prices move. Without this, every unchanged row is matched
    #: again from scratch: a trigram search, an alias lookup, a review
    #: row written, roughly four database round trips each, for an answer
    #: that cannot have changed. On a 10,000-line weekly file that is
    #: tens of thousands of round trips to re-derive last week's result.
    #:
    #: WHY A HASH RATHER THAN COMPARING FIELDS. Two of the four inputs --
    #: barcode and brand -- are NOT COLUMNS ON THIS TABLE. They arrive
    #: with the import row, are used for matching, and are not stored, so
    #: "did the barcode change" is unanswerable by comparison. A hash of
    #: everything matching was given answers it exactly, and keeps
    #: answering it when a fifth input is added.
    #:
    #: NULLABLE, and null means "never matched, or matched before this
    #: existed" -- both of which correctly mean "match it again".
    match_fingerprint = db.Column(db.String(64), nullable=True)

    sku = db.Column(db.String(50), nullable=False)
    product_code = db.Column(db.String(20), nullable=False)
