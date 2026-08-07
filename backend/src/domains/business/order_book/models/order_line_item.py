"""
OrderLineItem -- one line on an order. Free-text description only, no
product catalogue dependency -- matches the approved plan's decision #2
and the frontend's OrderLineItem shape.

line_total_cents is computed once at creation (quantity * unit_price)
and stored -- an order's line items are never edited after creation in
this feature (only the order's STATUS changes), so there's no
drift risk to guard against by re-deriving it on every read.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class OrderLineItem(BaseModel):
    __tablename__ = "order_book_line_items"
    __table_args__ = (
        db.Index("ix_order_book_line_items_order_id", "order_id"),
        db.CheckConstraint("quantity > 0", name="ck_order_book_line_items_positive_quantity"),
        db.CheckConstraint("unit_price_cents >= 0", name="ck_order_book_line_items_non_negative_price"),
        {"schema": "business"},
    )

    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey("business.order_book_orders.id"), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Integer(), nullable=False)
    unit_price_cents = db.Column(db.BigInteger, nullable=False)
    line_total_cents = db.Column(db.BigInteger, nullable=False)
