"""
Order data access. Same ownership-filtering discipline as Loan Book's
CustomerRepository/LoanRepository -- see those files' docstrings.
EVERY read method takes business_id and filters by it; there is no
method here that can return an order without being told which business
is asking.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import List, Optional

from src.domains.business.order_book.models.order import Order, OrderStatus
from src.extensions import db


class OrderRepository:
    @staticmethod
    def create(order: Order) -> Order:
        db.session.add(order)
        db.session.flush()
        return order

    @staticmethod
    def get_by_id(order_id: uuid.UUID, business_id: uuid.UUID) -> Optional[Order]:
        """Returns None for 'doesn't exist', 'deleted', and 'belongs to
        a different business' identically -- see OrderBookNotFoundError's
        docstring for why this ambiguity is deliberate."""
        return Order.query.filter_by(id=order_id, business_id=business_id, is_deleted=False).first()

    @staticmethod
    def list_for_business(
        business_id: uuid.UUID, status: Optional[OrderStatus] = None
    ) -> List[Order]:
        query = Order.query.filter_by(business_id=business_id, is_deleted=False)
        if status is not None:
            query = query.filter_by(status=status)
        return query.order_by(Order.created_at.desc()).all()

    @staticmethod
    def list_deleted_for_business(business_id: uuid.UUID) -> List[Order]:
        return Order.query.filter_by(business_id=business_id, is_deleted=True).all()

    @staticmethod
    def highest_order_number_for_date(business_id: uuid.UUID, order_date: date) -> int:
        """The current max order_number already used today for this
        business -- INCLUDES deleted/trashed orders, so a trashed
        order's number is never reused within the same day (avoiding a
        confusing 'two different orders, same #' situation even after
        one is trashed, per the approved per-day numbering plan)."""
        result = (
            db.session.query(db.func.max(Order.order_number))
            .filter(Order.business_id == business_id, Order.order_date == order_date)
            .scalar()
        )
        return result or 0

    @staticmethod
    def list_due_for_auto_clear(business_id: uuid.UUID, status: OrderStatus) -> List[Order]:
        """All active (non-deleted) orders of the given status -- the
        actual time-window filtering happens in the service layer
        (services/auto_clear_service.py), which is pure and unit-testable
        without a database."""
        return Order.query.filter_by(business_id=business_id, status=status, is_deleted=False).all()
