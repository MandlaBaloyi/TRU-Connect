"""
Inventory -- "how much of each product can I currently sell", the real
table behind the frontend's own already-built Inventory feature (see
frontend/src/features/dashboard/supplier/inventory/types.ts's own
docstring for the full architecture this was built against).

NEVER DUPLICATES PRODUCT DATA -- no name/price/category live here,
only product_id (a real FK) plus quantity. Matches the frontend's own
explicit design principle exactly.

quantity_reserved EXISTS BUT NOTHING SETS IT YET -- schema-ready for
when Orders can actually reserve stock against a real order, same
"add the field while cheap, wire the behaviour later" pattern as
Product.unit_quantity/unit_measure. No reservation LOGIC exists here
because there's nothing to reserve against.

InventorySettings is deliberately its OWN table, not columns bolted
onto supplier_profiles -- confirmed during planning review: keeps
Inventory's own schema self-contained, and future settings
(allow_backorders, auto_reserve_on_order) land here without touching
another domain's table.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class LowStockAlertChannel(str, enum.Enum):
    """Matches the frontend's own LowStockAlertChannel exactly. Same
    name==value convention as Product's own enums, same reasoning
    (see that model's own ProductCategory docstring)."""

    IN_APP = "IN_APP"
    EMAIL = "EMAIL"


class Inventory(BaseModel):
    __tablename__ = "inventory"
    __table_args__ = (
        db.Index("ix_inventory_supplier_profile_id", "supplier_profile_id"),
        {"schema": "supplier"},
    )

    product_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("supplier.products.id"),
        nullable=False,
        unique=True,  # one inventory record per product, enforced at the DB level
    )
    # Denormalized, matching Product.supplier_profile_id's own
    # reasoning -- lets ownership checks (and the future summary/list
    # queries) filter by supplier without a join through products.
    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    quantity_on_hand = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    quantity_reserved = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=5, server_default=db.text("5"))


class InventorySettings(BaseModel):
    __tablename__ = "inventory_settings"
    __table_args__ = ({"schema": "supplier"},)

    supplier_profile_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("supplier.supplier_profiles.id"),
        nullable=False,
        unique=True,
    )
    default_low_stock_threshold = db.Column(db.Integer, nullable=False, default=5, server_default=db.text("5"))
    low_stock_alert_channel = db.Column(
        db.Enum(LowStockAlertChannel, name="low_stock_alert_channel", schema="supplier"),
        nullable=False,
        default=LowStockAlertChannel.IN_APP,
        server_default=LowStockAlertChannel.IN_APP.value,
    )
