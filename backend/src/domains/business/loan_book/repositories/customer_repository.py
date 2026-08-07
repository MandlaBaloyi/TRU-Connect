"""
Customer data access.

EVERY read method here takes business_id and filters by it -- this is
NOT optional or a convenience parameter. It's the actual mechanism that
makes cross-business data leakage structurally impossible rather than
merely policy: there is no method on this class that can return a
customer without being told which business is asking.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from src.domains.business.loan_book.models.customer import Customer
from src.extensions import db


class CustomerRepository:
    @staticmethod
    def create(customer: Customer) -> Customer:
        db.session.add(customer)
        db.session.flush()
        return customer

    @staticmethod
    def get_by_id(customer_id: uuid.UUID, business_id: uuid.UUID) -> Optional[Customer]:
        """Returns None if the customer doesn't exist, is deleted, OR
        belongs to a different business -- all three cases look
        identical to the caller on purpose. A 404 for 'not yours' and a
        404 for 'doesn't exist' must be indistinguishable, or the
        response itself leaks whether a given ID is real."""
        return Customer.query.filter_by(
            id=customer_id, business_id=business_id, is_deleted=False
        ).first()

    @staticmethod
    def list_for_business(business_id: uuid.UUID) -> List[Customer]:
        return Customer.query.filter_by(business_id=business_id, is_deleted=False).all()

    @staticmethod
    def list_deleted_for_business(business_id: uuid.UUID) -> List[Customer]:
        return Customer.query.filter_by(business_id=business_id, is_deleted=True).all()

    @staticmethod
    def search(business_id: uuid.UUID, term: str) -> List[Customer]:
        pattern = f"%{term}%"
        return Customer.query.filter(
            Customer.business_id == business_id,
            Customer.is_deleted == False,  # noqa: E712
            db.or_(Customer.name.ilike(pattern), Customer.phone.ilike(pattern)),
        ).all()
