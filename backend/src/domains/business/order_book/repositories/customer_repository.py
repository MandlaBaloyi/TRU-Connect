"""
OrderBookCustomer data access. Same ownership-filtering discipline as
every other repository in this project -- EVERY read method takes
business_id and filters by it.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from src.domains.business.order_book.models.customer import OrderBookCustomer
from src.extensions import db


class CustomerRepository:
    @staticmethod
    def create(customer: OrderBookCustomer) -> OrderBookCustomer:
        db.session.add(customer)
        db.session.flush()
        return customer

    @staticmethod
    def get_by_id(customer_id: uuid.UUID, business_id: uuid.UUID) -> Optional[OrderBookCustomer]:
        """Returns None for 'doesn't exist', 'deleted', and 'belongs to
        a different business' identically -- see OrderBookNotFoundError's
        docstring for why this ambiguity is deliberate."""
        return OrderBookCustomer.query.filter_by(
            id=customer_id, business_id=business_id, is_deleted=False
        ).first()

    @staticmethod
    def list_for_business(business_id: uuid.UUID) -> List[OrderBookCustomer]:
        return OrderBookCustomer.query.filter_by(business_id=business_id, is_deleted=False).all()

    @staticmethod
    def list_deleted_for_business(business_id: uuid.UUID) -> List[OrderBookCustomer]:
        return OrderBookCustomer.query.filter_by(business_id=business_id, is_deleted=True).all()

    @staticmethod
    def search(business_id: uuid.UUID, term: str) -> List[OrderBookCustomer]:
        pattern = f"%{term}%"
        return OrderBookCustomer.query.filter(
            OrderBookCustomer.business_id == business_id,
            OrderBookCustomer.is_deleted == False,  # noqa: E712
            db.or_(OrderBookCustomer.name.ilike(pattern), OrderBookCustomer.phone.ilike(pattern)),
        ).all()
