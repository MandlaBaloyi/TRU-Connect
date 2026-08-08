"""
Customer -- a person a business extends credit to. Matches the
frontend's types.ts Customer shape field-for-field.

TABLE NAME: loan_book_customers, not the old generic `customers`.
Originally left unprefixed on the reasoning that it was a genuine
shared business-level identity other features would reference too --
that assumption changed once Order Book was built with its own fully
independent `order_book_customers` table instead of sharing this one.
With nothing left actually sharing it, an unprefixed `customers` table
sitting in the shared `business` schema was just a naming inconsistency
against every other feature-owned table. Renamed via
migrations/versions/<see migration file> using op.rename_table(), not
drop-and-recreate -- preserves every existing row exactly as-is.

business_id is the OWNERSHIP field this whole feature's authorization
model rests on -- every repository method that lists/reads a customer
filters by it, and it's the field the IDOR test (see
tests/domains/business/loan_book/test_ownership.py) exists to prove is
actually enforced, not just present.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class Customer(BaseModel):
    __tablename__ = "loan_book_customers"
    __table_args__ = (
        db.Index("ix_loan_book_customers_business_id", "business_id"),
        db.Index("ix_loan_book_customers_business_id_deleted", "business_id", "is_deleted"),
        {"schema": "business"},
    )

    business_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False
    )
    name = db.Column(db.String(200), nullable=False)
    # Optional by design (Doc 04 §3.4) -- many informal customers are
    # known by name and face only.
    phone = db.Column(db.String(20), nullable=True)
    first_recorded_at = db.Column(db.DateTime(timezone=True), nullable=False)
    last_transaction_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # is_deleted / deleted_at inherited from BaseModel -- customers are
    # soft-deleted (Doc 06 §17), matching the frontend's Trash feature.
    deletion_reason = db.Column(db.String(500), nullable=True)
