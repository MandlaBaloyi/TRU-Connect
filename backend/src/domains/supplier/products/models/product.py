"""
Product -- grown from the deliberately minimal slice that only existed
to give the ordering gate something real to count (see git history /
this file's own previous docstring for that reasoning, still valid:
that gate is why a Product model existed at all before this round).

This is now the real thing: name, category, price, selling unit, the
unit_quantity/unit_measure pair ("1 Case = 24 Bottles" math), and
archive state -- matching the frontend's own already-locked contract
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

Deliberately in the `supplier` schema (supplier.products), matching
supplier.supplier_profiles' own placement.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class ProductCategory(str, enum.Enum):
    """TRU-Connect-controlled taxonomy, matching the frontend's own
    CATEGORY_OPTIONS exactly (16 values). Every member's NAME equals
    its VALUE (e.g. BEVERAGES = "BEVERAGES") -- deliberately, not by
    accident: SQLAlchemy's Enum(PyEnumClass) persists the member's
    .name to Postgres, not its .value. This codebase already hit that
    exact mismatch once (ConnectionRequestStatus, whose lowercase
    values differ from its uppercase names, needed the Postgres enum's
    stored values corrected to match what actually gets persisted).
    Keeping name == value here sidesteps that whole class of bug by
    construction, and it also means the string this returns over the
    API is exactly what the frontend's own ProductCategory union
    expects -- no lowercase/uppercase translation layer needed
    anywhere.
    """

    FOOD_GROCERY = "FOOD_GROCERY"
    BEVERAGES = "BEVERAGES"
    SNACKS_CONFECTIONERY = "SNACKS_CONFECTIONERY"
    BAKERY = "BAKERY"
    DAIRY_CHILLED = "DAIRY_CHILLED"
    FRESH_PRODUCE = "FRESH_PRODUCE"
    MEAT_FROZEN = "MEAT_FROZEN"
    HOUSEHOLD_CLEANING = "HOUSEHOLD_CLEANING"
    PERSONAL_CARE = "PERSONAL_CARE"
    BABY_FAMILY = "BABY_FAMILY"
    STATIONERY_SCHOOL = "STATIONERY_SCHOOL"
    HARDWARE_GENERAL = "HARDWARE_GENERAL"
    ELECTRONICS_ACCESSORIES = "ELECTRONICS_ACCESSORIES"
    PACKAGING_DISPOSABLE = "PACKAGING_DISPOSABLE"
    CLOTHING_APPAREL = "CLOTHING_APPAREL"
    OTHER = "OTHER"


class ProductUnit(str, enum.Enum):
    """Matches the frontend's own UNIT_OPTIONS exactly (12 values).
    Same name==value convention as ProductCategory, same reasoning.
    Used for BOTH selling_unit and unit_measure -- one enum, two
    columns, matching the frontend's own single ProductUnit type
    serving both roles."""

    EACH = "EACH"
    PACK = "PACK"
    BOX = "BOX"
    CASE = "CASE"
    BAG = "BAG"
    BOTTLE = "BOTTLE"
    CAN = "CAN"
    DOZEN = "DOZEN"
    KG = "KG"
    G = "G"
    L = "L"
    ML = "ML"


class Product(BaseModel):
    __tablename__ = "products"
    __table_args__ = (
        db.Index("ix_products_supplier_profile_id", "supplier_profile_id"),
        # Matches the Products list screen's own real query shape
        # (supplier's own products, excluding archived, newest first) --
        # named explicitly rather than left for the query planner to
        # discover under load.
        db.Index("ix_products_supplier_profile_id_is_archived", "supplier_profile_id", "is_archived"),
        # product_code is PLATFORM-WIDE unique -- it's the short,
        # human-readable stand-in for this row's own UUID, shown to
        # both the supplier and any business ordering from them (see
        # algorithms/product_code_generator.py's own docstring).
        db.UniqueConstraint("product_code", name="uq_products_product_code"),
        # sku is unique per SUPPLIER, not platform-wide -- matches how
        # SKUs actually work in the real world; every business has its
        # own numbering, with no expectation two unrelated suppliers
        # never reuse the same label (see algorithms/sku_generator.py's
        # own docstring).
        db.UniqueConstraint("supplier_profile_id", "sku", name="uq_products_supplier_profile_id_sku"),
        {"schema": "supplier"},
    )

    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
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
    sku = db.Column(db.String(50), nullable=False)
    product_code = db.Column(db.String(20), nullable=False)
