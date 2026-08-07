"""
Payment data access.

NO business_id filter here -- see the model's own docstring for why.
Every method takes the ALREADY-AUTHORIZED loan_entry_id as its scoping
key; the service layer is responsible for confirming that entry belongs
to the requesting business BEFORE ever calling into this repository.
"""
from __future__ import annotations

import uuid
from typing import List

from src.domains.business.loan_book.models.payment import Payment
from src.extensions import db


class PaymentRepository:
    @staticmethod
    def create(payment: Payment) -> Payment:
        db.session.add(payment)
        db.session.flush()
        return payment

    @staticmethod
    def list_for_entry(loan_entry_id: uuid.UUID) -> List[Payment]:
        return Payment.query.filter_by(loan_entry_id=loan_entry_id).order_by(Payment.paid_at).all()

    @staticmethod
    def list_for_entries(loan_entry_ids: List[uuid.UUID]) -> List[Payment]:
        if not loan_entry_ids:
            return []
        return Payment.query.filter(Payment.loan_entry_id.in_(loan_entry_ids)).all()

    @staticmethod
    def delete(payment: Payment) -> None:
        """Genuine hard delete -- see Payment model's docstring for why
        this differs from Customer/LoanEntry's soft-delete."""
        db.session.delete(payment)
        db.session.flush()
