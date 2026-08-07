"""
LoanEntry data access. Same ownership-filtering discipline as
CustomerRepository -- see that file's docstring.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from src.domains.business.loan_book.models.loan_entry import LoanEntry
from src.extensions import db


class LoanRepository:
    @staticmethod
    def create(entry: LoanEntry) -> LoanEntry:
        db.session.add(entry)
        db.session.flush()
        return entry

    @staticmethod
    def get_by_id(entry_id: uuid.UUID, business_id: uuid.UUID) -> Optional[LoanEntry]:
        return LoanEntry.query.filter_by(
            id=entry_id, business_id=business_id, is_deleted=False
        ).first()

    @staticmethod
    def list_for_business(business_id: uuid.UUID) -> List[LoanEntry]:
        return LoanEntry.query.filter_by(business_id=business_id, is_deleted=False).all()

    @staticmethod
    def list_for_customer(customer_id: uuid.UUID, business_id: uuid.UUID) -> List[LoanEntry]:
        """Still filtered by business_id even though customer_id alone
        would usually be enough -- defence in depth: even if a caller
        somehow obtained another business's customer_id, this can never
        return that customer's entries without ALSO matching business_id."""
        return LoanEntry.query.filter_by(
            customer_id=customer_id, business_id=business_id, is_deleted=False
        ).all()

    @staticmethod
    def list_deleted_for_business(business_id: uuid.UUID) -> List[LoanEntry]:
        return LoanEntry.query.filter_by(business_id=business_id, is_deleted=True).all()

    @staticmethod
    def list_for_customer_including_deleted(customer_id: uuid.UUID, business_id: uuid.UUID) -> List[LoanEntry]:
        """For trash-summary purposes -- mirrors the frontend
        repository's listEntriesForCustomerIncludingDeleted()."""
        return LoanEntry.query.filter_by(customer_id=customer_id, business_id=business_id).all()
