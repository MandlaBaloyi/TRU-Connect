"""
Product -- the minimal slice of the future Catalogue domain. NOT the
full feature (no price, description, images, categories, or stock
levels yet) -- this exists right now for exactly one honest reason:
the ordering gate agreed during architecture review needs a REAL
question to ask, not a hypothetical one. "Can this business order
from this supplier" depends on two things being true -- an ACTIVE
connection AND the supplier having at least one real product -- and
that second half is meaningless without something real to count.

Deliberately in the `supplier` schema (supplier.products), matching
supplier.supplier_profiles' own placement -- a product belongs to a
supplier's own catalogue, the same ownership shape as everything else
supplier-owned in this codebase.

WHAT'S MISSING ON PURPOSE, not forgotten: price, description, images,
categories, stock/quantity tracking. Full Catalogue (search's own
"view products" tap resolving to a real, rich screen) is the next
major feature after this round -- this model is the foundation it
builds on, not a replacement for building it properly.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class Product(BaseModel):
    __tablename__ = "products"
    __table_args__ = (
        db.Index("ix_products_supplier_profile_id", "supplier_profile_id"),
        {"schema": "supplier"},
    )

    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    name = db.Column(db.String(200), nullable=False)
