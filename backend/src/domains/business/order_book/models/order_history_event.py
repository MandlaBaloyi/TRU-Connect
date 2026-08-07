"""
OrderHistoryEvent -- an append-only log of everything that happens in a
business's Order Book. Same reasoning as Loan Book's LoanHistoryEvent
for why this isn't shared.audit -- see that file's docstring. This is
Order Book's own copy of the same architecture decision, not a
duplication of Loan Book's actual table (each feature's history is
scoped to its own domain of events).
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import utcnow
from src.extensions import db


class OrderHistoryEventType(str, enum.Enum):
    ORDER_CREATED = "order_created"
    ORDER_COMPLETED = "order_completed"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_DELETED = "order_deleted"
    ORDER_RESTORED = "order_restored"
    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_DELETED = "customer_deleted"
    CUSTOMER_RESTORED = "customer_restored"


class OrderHistoryEvent(db.Model):
    __tablename__ = "order_book_history_events"
    __table_args__ = (
        db.Index("ix_order_book_history_business_id", "business_id"),
        db.Index("ix_order_book_history_business_id_occurred", "business_id", "occurred_at"),
        {"schema": "business"},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)
    customer_id = db.Column(UUID(as_uuid=True), nullable=False)
    order_id = db.Column(UUID(as_uuid=True), nullable=True)
    event_type = db.Column(
        db.Enum(
            OrderHistoryEventType,
            name="order_book_history_event_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    amount_cents = db.Column(db.BigInteger, nullable=True)
    reason = db.Column(db.String(500), nullable=True)
    occurred_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
