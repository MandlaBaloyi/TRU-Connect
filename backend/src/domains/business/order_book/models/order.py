"""
Order -- one customer order. Matches the frontend's Order shape.

business_id is DENORMALIZED here (also reachable via customer_id ->
Customer.business_id) -- same reasoning as Loan Book's LoanEntry: every
authorization check needs a single indexed WHERE clause, not a join.

order_number is UNIQUE ONLY WITHIN (business_id, order_date), not
globally -- see the composite index/constraint below. The real row
identity is `id` (a UUID); order_number + order_date together are a
display/lookup convenience only, exactly matching the frontend's
Order.orderNumber docstring in types.ts. total_cents is computed once
at creation from the order's line items and stored (not re-derived on
every read like Loan Book's outstanding balance) -- an order's total
doesn't change after creation the way a debt's outstanding balance
does with each new payment, so there's nothing here that can drift.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderDeletionReason(str, enum.Enum):
    """Distinguishes a shop owner's own deletion from an automatic
    sweep -- see the frontend's TrashReason for the matching concept.
    MANUAL_CLEAR_COMPLETED covers the bulk 'clear all completed' action;
    AUTO_CLEAR_COMPLETED/AUTO_CLEAR_CANCELLED cover the scheduled sweep
    (see services/auto_clear_service.py)."""

    MANUAL_DELETE = "manual_delete"
    MANUAL_CLEAR_COMPLETED = "manual_clear_completed"
    AUTO_CLEAR_COMPLETED = "auto_clear_completed"
    AUTO_CLEAR_CANCELLED = "auto_clear_cancelled"


class Order(BaseModel):
    __tablename__ = "order_book_orders"
    __table_args__ = (
        db.Index("ix_order_book_orders_business_id", "business_id"),
        db.Index("ix_order_book_orders_business_id_deleted", "business_id", "is_deleted"),
        db.Index("ix_order_book_orders_customer_id", "customer_id"),
        db.Index("ix_order_book_orders_business_id_status", "business_id", "status"),
        # Enforces the per-day numbering rule at the database level, not
        # just in application code -- see module docstring.
        db.UniqueConstraint(
            "business_id", "order_date", "order_number", name="uq_order_book_orders_business_date_number"
        ),
        db.CheckConstraint("total_cents >= 0", name="ck_order_book_orders_non_negative_total"),
        {"schema": "business"},
    )

    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("business.order_book_customers.id"), nullable=False)
    order_date = db.Column(db.Date(), nullable=False)
    order_number = db.Column(db.Integer(), nullable=False)
    status = db.Column(
        db.Enum(OrderStatus, name="order_book_order_status", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=OrderStatus.PENDING,
    )
    total_cents = db.Column(db.BigInteger, nullable=False)
    notes = db.Column(db.String(500), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    cancelled_at = db.Column(db.DateTime(timezone=True), nullable=True)
    cancellation_reason = db.Column(db.String(500), nullable=True)
    # is_deleted / deleted_at inherited from BaseModel.
    deletion_reason = db.Column(db.String(500), nullable=True)
    deletion_cause = db.Column(
        db.Enum(
            OrderDeletionReason,
            name="order_book_deletion_cause",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=True,
    )
