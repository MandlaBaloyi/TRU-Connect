"""
SupplierPinnedProduct -- a supplier's hand-picked "feature these on my
business profile" products. A join row between supplier_profiles and
products (both in the `supplier` schema); real FKs to each, not a
polymorphic pair.

Lives in supplier_profile/, not products/ -- this is profile CURATION
(what a business sees on the supplier's brand page), not a property of
the product itself. products/ stays unaware pinning exists beyond
surfacing an `is_pinned` flag on its own DTO, which it computes from a
set this repository hands it.

pin_order is the display order on the profile strip -- a plain
append-on-pin integer for now (newest pin last). A drag-to-reorder
picker is a later refinement; nothing here blocks it.

MAX 6 pinned is enforced in pinned_products_service, not by a DB
constraint -- it's a business rule that may move by tier later, same
reasoning as products' own per-tier photo limits.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class SupplierPinnedProduct(BaseModel):
    __tablename__ = "supplier_pinned_products"
    __table_args__ = (
        db.UniqueConstraint(
            "supplier_profile_id", "product_id", name="uq_supplier_pinned_products_unique"
        ),
        db.Index("ix_supplier_pinned_products_profile_id", "supplier_profile_id"),
        {"schema": "supplier"},
    )

    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey("supplier.supplier_offers.id"), nullable=False)
    pin_order = db.Column(db.Integer, nullable=False, default=0)
