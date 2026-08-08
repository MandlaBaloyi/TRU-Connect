"""
OrderBookCustomer -- Order Book's OWN customer record, independent of
Loan Book's `business.loan_book_customers` table.

THIS REPLACES THE EARLIER "reuse Loan Book's Customer" decision. That
was flagged explicitly for review; the answer was "no, keep them
independent" -- so this is now its own table, `order_book_customers`,
never referenced by Loan Book and never referencing it. Deleting or
changing a customer here has zero effect on Loan Book, and vice versa.
Same field shape as Loan Book's Customer (name/phone/soft-delete) --
that's the two features happening to model "a customer" the same way,
not a coupling between them.

business_id is the OWNERSHIP field this feature's authorization model
rests on -- same discipline as every other model in this project.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class OrderBookCustomer(BaseModel):
    __tablename__ = "order_book_customers"
    __table_args__ = (
        db.Index("ix_order_book_customers_business_id", "business_id"),
        db.Index("ix_order_book_customers_business_id_deleted", "business_id", "is_deleted"),
        {"schema": "business"},
    )

    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    first_recorded_at = db.Column(db.DateTime(timezone=True), nullable=False)
    last_transaction_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # is_deleted / deleted_at inherited from BaseModel.
    deletion_reason = db.Column(db.String(500), nullable=True)
