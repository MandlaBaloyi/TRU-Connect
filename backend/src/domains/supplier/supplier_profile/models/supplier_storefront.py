"""
The supplier's own merchandising of their brand profile: which
storefront sections run, in what order, and -- for the two the
platform cannot compute -- which products are in them.

WHY A TABLE AND NOT COLUMNS ON supplier_profiles. Four of the six
sections are COMPUTED (on sale, best sellers, bulk value, just added):
the platform derives them from product data and the supplier only
decides whether to show them. Two are CHOSEN (a featured pick, a
curated strip): only the person selling knows what belongs in them,
and a curated strip can exist more than once -- "Stock up for
month-end" and "Braai weekend" are two different strips a supplier may
well want at the same time. Booleans on the profile row could express
the first kind and never the second.

ORDER IS DATA, NOT CODE. `position` is what lets a wholesaler put
their promoted range above the fold without an app release -- the same
reason the feed contract is server-driven (see the frontend's
storefront/types.ts). Hard-coding the order in the service would put
every merchandising conversation behind a deploy.

A SUPPLIER WITH NO ROWS STILL HAS A STOREFRONT. The service falls back
to a sensible default set rather than creating rows on read -- a
business browsing a profile must never write to the supplier's own
configuration as a side effect, the same rule
InventoryRepository.list_by_product_ids already documents for
inventory.

DELIBERATELY SEPARATE FROM supplier_pinned_products, which still does
its own different job: pinning floats a product to the front of its
CATEGORY strip, and says nothing about these sections.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class StorefrontSectionType(str, enum.Enum):
    """COMPUTED -- the platform derives the products; the supplier only
    chooses whether the section runs and where it sits."""

    ON_SALE = "ON_SALE"
    BEST_SELLERS = "BEST_SELLERS"
    BULK_VALUE = "BULK_VALUE"
    NEW_ARRIVALS = "NEW_ARRIVALS"

    """CHOSEN -- the supplier picks the products themselves. Anything
    below this line reads from supplier_storefront_section_products."""

    FEATURED_PRODUCT = "FEATURED_PRODUCT"
    CURATED = "CURATED"


#: The two types whose products come from the join table rather than a
#: query. Kept here beside the enum so a new type cannot be added
#: without deciding which kind it is.
CHOSEN_SECTION_TYPES = frozenset(
    {StorefrontSectionType.FEATURED_PRODUCT, StorefrontSectionType.CURATED}
)

#: Every other type is computed from the supplier's own catalogue.
COMPUTED_SECTION_TYPES = frozenset(set(StorefrontSectionType) - CHOSEN_SECTION_TYPES)


class SupplierStorefrontSection(BaseModel):
    __tablename__ = "supplier_storefront_sections"
    __table_args__ = (
        db.Index("ix_supplier_storefront_sections_profile_id", "supplier_profile_id"),
        {"schema": "supplier"},
    )

    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    section_type = db.Column(
        db.Enum(StorefrontSectionType, name="storefront_section_type", schema="supplier"),
        nullable=False,
    )
    # NO UNIQUE CONSTRAINT ON (profile, type), deliberately. A supplier
    # may run several CURATED strips at once, and a constraint that
    # only holds for four of the six types is a constraint the database
    # cannot express cleanly -- the service enforces one-per-type for
    # the computed kinds instead, where the rule actually lives.
    is_enabled = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    position = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    # Only ever set for CURATED -- the supplier's own words for their
    # own shelf ("Stock up for month-end"), with an optional second
    # line under it ("What sells out first after payday"). The computed
    # sections are titled by the platform, because the platform is the
    # one making the claim; a supplier's own shelf is the one place
    # they get to say why it exists.
    title = db.Column(db.String(60), nullable=True)
    subtitle = db.Column(db.String(80), nullable=True)


class SupplierStorefrontSectionProduct(BaseModel):
    """One product inside a CHOSEN section, in the supplier's own order.

    FEATURED_PRODUCT is a section with exactly one of these rather than
    a column somewhere -- so "the supplier picked this" is stored one
    way for both chosen sections, and a featured product can be
    reordered into or out of a curated strip without moving between
    two different storage shapes.
    """

    __tablename__ = "supplier_storefront_section_products"
    __table_args__ = (
        db.UniqueConstraint(
            "section_id", "product_id", name="uq_storefront_section_products_unique"
        ),
        db.Index("ix_storefront_section_products_section_id", "section_id"),
        {"schema": "supplier"},
    )

    section_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("supplier.supplier_storefront_sections.id"),
        nullable=False,
    )
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey("supplier.products.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0, server_default="0")
