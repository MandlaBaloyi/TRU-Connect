"""
Payment -- one repayment against a LoanEntry. Matches the frontend's
Payment shape.

DELIBERATELY NO business_id here, unlike Customer/LoanEntry: a payment
has no independent existence -- it only ever exists attached to one
LoanEntry, and every route that touches a payment already has to load
and authorize that parent entry first. Denormalizing business_id onto
Payment too would be a second copy of the same fact with no query it
actually speeds up, since a payment is never listed or searched
independently of its entry.

DELIBERATELY NO is_deleted use here either, even though BaseModel
provides the columns structurally (for schema consistency across every
model): the frontend's deletePayment() is a genuine hard delete, not a
soft one -- removing an accidentally-recorded payment is a correction,
not something that needs a 7-day recovery window the way removing a
whole entry does. The service layer enforces this distinction; the
columns existing on the model is harmless, unused dead weight for this
one table specifically.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class Payment(BaseModel):
    __tablename__ = "loan_book_payments"
    __table_args__ = (
        db.Index("ix_loan_book_payments_loan_entry_id", "loan_entry_id"),
        db.CheckConstraint("amount_cents > 0", name="ck_loan_book_payments_positive_amount"),
        {"schema": "business"},
    )

    loan_entry_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("business.loan_book_entries.id"), nullable=False
    )

    loan_entry_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("business.loan_book_entries.id"), nullable=False
    )
    amount_cents = db.Column(db.BigInteger, nullable=False)
    paid_at = db.Column(db.DateTime(timezone=True), nullable=False)
    note = db.Column(db.String(500), nullable=True)
