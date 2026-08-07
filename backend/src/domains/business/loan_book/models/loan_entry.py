"""
LoanEntry -- one credit sale. Matches the frontend's LoanEntry shape.

business_id is DENORMALIZED here (also present on Customer, which this
row belongs to via customer_id) -- deliberately, not accidentally. Every
authorization check on an entry needs to answer "does this belong to the
requesting business?" and doing that via a single indexed column beats
joining through Customer on every single request. The two values must
always agree; see the service layer's create_entry(), the only place
that ever sets both at once.

Money is BIGINT cents, never NUMERIC/DECIMAL/FLOAT -- see
shared/finance/README.md for the full reasoning. original_amount_cents
is immutable once set; the CURRENT outstanding balance is never stored
-- it's always derived from this row plus its Payments, exactly like the
frontend's balanceCalculator.ts already does. Storing a derived value
risks it silently drifting from the truth; deriving it every time makes
that drift structurally impossible.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class LoanEntry(BaseModel):
    __tablename__ = "loan_book_entries"
    __table_args__ = (
        db.Index("ix_loan_book_entries_business_id", "business_id"),
        db.Index("ix_loan_book_entries_business_id_deleted", "business_id", "is_deleted"),
        db.Index("ix_loan_book_entries_customer_id", "customer_id"),
        db.CheckConstraint("original_amount_cents > 0", name="ck_loan_book_entries_positive_amount"),
        {"schema": "business"},
    )

    business_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False
    )
    customer_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("business.loan_book_customers.id"), nullable=False
    )
    original_amount_cents = db.Column(db.BigInteger, nullable=False)
    sale_date = db.Column(db.DateTime(timezone=True), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    is_settled = db.Column(db.Boolean, nullable=False, default=False)
    settled_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # is_deleted / deleted_at inherited from BaseModel.
    deletion_reason = db.Column(db.String(500), nullable=True)