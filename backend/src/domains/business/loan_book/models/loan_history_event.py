"""
LoanHistoryEvent -- an append-only log of everything that happens in a
business's Loan Book: sales, payments, deletions, restores, receipt
interactions.


same call the frontend already made for the same reason -- and it means
the eventual merge is a deliberate architecture decision made by someone
who can see both real systems at once, not an accidental one made by
someone guessing at half of it.

business_id is present here too, same ownership-filtering discipline as
every other model in this feature.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.core.base_model import utcnow
from src.extensions import db


class LoanHistoryEventType(str, enum.Enum):
    SALE_CREATED = "sale_created"
    PAYMENT_RECORDED = "payment_recorded"
    PAYMENT_REMOVED = "payment_removed"
    ENTRY_DELETED = "entry_deleted"
    ENTRY_RESTORED = "entry_restored"
    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_DELETED = "customer_deleted"
    CUSTOMER_RESTORED = "customer_restored"
    RECEIPT_VIEWED = "receipt_viewed"
    RECEIPT_SHARED = "receipt_shared"


# The subset shown on the customer-facing Transaction History screen --
# mirrors the frontend's TRANSACTION_EVENT_TYPES exactly (same reasoning:
# a bank statement shows money movements, not "card deleted").
TRANSACTION_EVENT_TYPES = frozenset({
    LoanHistoryEventType.SALE_CREATED,
    LoanHistoryEventType.PAYMENT_RECORDED,
    LoanHistoryEventType.PAYMENT_REMOVED,
})




class LoanHistoryEvent(db.Model):
    __tablename__ = "loan_book_history_events"
    __table_args__ = (
        db.Index("ix_loan_book_history_business_id", "business_id"),
        db.Index("ix_loan_book_history_business_id_occurred", "business_id", "occurred_at"),
   
        {"schema": "business"},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)
    customer_id = db.Column(UUID(as_uuid=True), nullable=False)
    loan_entry_id = db.Column(UUID(as_uuid=True), nullable=True)
    event_type = db.Column(
        db.Enum(
            LoanHistoryEventType,
            name="loan_book_history_event_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    amount_cents = db.Column(db.BigInteger, nullable=True)
    description = db.Column(db.String(500), nullable=True)
    reason = db.Column(db.String(500), nullable=True)
    event_metadata = db.Column("metadata", JSONB, nullable=False, default=dict)
    occurred_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)