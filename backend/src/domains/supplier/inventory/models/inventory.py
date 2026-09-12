"""
Inventory -- "how much of each product can I currently sell", the real
table behind the frontend's own already-built Inventory feature (see
frontend/src/features/dashboard/supplier/inventory/types.ts's own
docstring for the full architecture this was built against).

NEVER DUPLICATES PRODUCT DATA -- no name/price/category live here,
only product_id (a real FK) plus quantity. Matches the frontend's own
explicit design principle exactly.

quantity_reserved -- REAL, WIRED as of checkout_service.py's own
submit_checkout: incremented via InventoryRepository.reserve_quantity
the moment a real order is placed, matching this field's own original
"schema-ready for when Orders can actually reserve stock" intent from
when it was first added. Releasing a reservation when a supplier
declines an order is real, separate, later work -- reserve_quantity
already supports it (a negative delta), just not called from anywhere
yet.

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
from src.shared.constants.write_source import WriteSource


class LowStockAlertChannel(str, enum.Enum):
    """Matches the frontend's own LowStockAlertChannel exactly. Same
    name==value convention as SupplierOffer's own enums, same reasoning
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
        db.ForeignKey("supplier.supplier_offers.id"),
        nullable=False,
        unique=True,  # one inventory record per product, enforced at the DB level
    )
    # Denormalized, matching SupplierOffer.supplier_profile_id's own
    # reasoning -- lets ownership checks (and the future summary/list
    # queries) filter by supplier without a join through products.
    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    quantity_on_hand = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    quantity_reserved = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=5, server_default=db.text("5"))

    #: WHICH CHANNEL last wrote this row -- see
    #: shared/constants/write_source.py for the full reasoning.
    #:
    #: NOT NULLABLE, defaulting to APP. Every row that existed before
    #: this column did was written by a person in the app, because no
    #: other channel could write one -- so APP is the honest backfill
    #: rather than a guess, and a nullable column would only invite
    #: "unknown" handling for a state that never occurs.
    source = db.Column(
        db.Enum(WriteSource, name="write_source", schema="supplier"),
        nullable=False,
        default=WriteSource.APP,
        server_default=WriteSource.APP.value,
    )



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
