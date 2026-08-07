"""
Ownership / IDOR tests -- service layer. Same shape and same reasoning
as loan_book/test_ownership.py: Business A creates real data, Business
B -- a completely separate, real business owner -- tries to read,
modify, or delete it using A's REAL id. Every attempt must fail
identically to how a non-existent id would fail (OrderBookNotFoundError).

Includes the sharpest case Loan Book's own suite calls out explicitly:
an actual POST attempting to create an order against a customer the
caller has no relationship to.

NOT YET RUN in this environment -- see conftest.py's docstring.
"""
from __future__ import annotations

import uuid

import pytest

from src.domains.business.order_book.models.customer import OrderBookCustomer
from src.domains.business.order_book.repositories.customer_repository import CustomerRepository
from src.domains.business.order_book.services.errors import (
    OrderBookInvalidTransitionError,
    OrderBookNotFoundError,
)
from src.domains.business.order_book.services.order_book_service import OrderBookService, OrderLineItemInput
from src.shared.finance import Money


def _make_line_items():
    return [OrderLineItemInput(description="Big Boss Kota", quantity=1, unit_price=Money(6500))]


@pytest.fixture()
def business_a(make_business_user):
    return make_business_user("order-book-a@example.com")


@pytest.fixture()
def business_b(make_business_user):
    return make_business_user("order-book-b@example.com")


@pytest.fixture()
def business_a_customer(business_a, db_session):
    from datetime import datetime, timezone

    customer = OrderBookCustomer(
        id=uuid.uuid4(),
        business_id=business_a.id,
        name="Mandla (A's customer)",
        phone="0821234567",
        first_recorded_at=datetime.now(timezone.utc),
    )
    CustomerRepository.create(customer)
    db_session.commit()
    return customer


@pytest.fixture()
def business_a_order(business_a, business_a_customer):
    return OrderBookService.create_order(
        business_a.id, _make_line_items(), customer_id=business_a_customer.id,
    )


class TestOrderOwnership:
    def test_business_b_cannot_read_business_a_order(self, business_b, business_a_order):
        with pytest.raises(OrderBookNotFoundError):
            OrderBookService.get_order(business_b.id, business_a_order.id)

    def test_business_b_order_list_never_includes_business_a_orders(self, business_b, business_a_order):
        """Not just 'direct fetch by ID fails' -- the LIST endpoint
        must never leak another business's rows either, a separate
        code path from get_by_id()."""
        views = OrderBookService.list_orders(business_b.id)
        order_ids = {v.order.id for v in views}
        assert business_a_order.id not in order_ids

    def test_business_a_can_read_their_own_order(self, business_a, business_a_order):
        """The negative-case tests above are only meaningful alongside
        this: proving the legitimate owner isn't accidentally blocked
        too."""
        view = OrderBookService.get_order(business_a.id, business_a_order.id)
        assert view.order.id == business_a_order.id

    def test_business_b_cannot_complete_business_a_order(self, business_b, business_a_order):
        with pytest.raises(OrderBookNotFoundError):
            OrderBookService.complete_order(business_b.id, business_a_order.id)

    def test_business_b_cannot_cancel_business_a_order(self, business_b, business_a_order):
        with pytest.raises(OrderBookNotFoundError):
            OrderBookService.cancel_order(business_b.id, business_a_order.id, reason="not yours")

    def test_business_b_cannot_delete_business_a_order(self, business_b, business_a_order):
        with pytest.raises(OrderBookNotFoundError):
            OrderBookService.delete_order(business_b.id, business_a_order.id)

    def test_business_b_cannot_restore_business_a_deleted_order(self, business_a, business_b, business_a_order):
        OrderBookService.delete_order(business_a.id, business_a_order.id)
        with pytest.raises(OrderBookNotFoundError):
            OrderBookService.restore_order(business_b.id, business_a_order.id)

    def test_business_b_cannot_create_order_against_business_a_customer(self, business_b, business_a_customer):
        """The sharpest case, matching Loan Book's own suite: an actual
        POST attempting to place an order against a customer the
        caller has no relationship to must fail exactly like the
        customer doesn't exist."""
        with pytest.raises(OrderBookNotFoundError):
            OrderBookService.create_order(
                business_b.id, _make_line_items(), customer_id=business_a_customer.id,
            )


class TestCustomerOwnership:
    def test_business_b_cannot_read_business_a_customer(self, business_b, business_a_customer):
        with pytest.raises(OrderBookNotFoundError):
            OrderBookService.get_customer(business_b.id, business_a_customer.id)

    def test_business_b_cannot_delete_business_a_customer(self, business_b, business_a_customer):
        with pytest.raises(OrderBookNotFoundError):
            OrderBookService.delete_customer(business_b.id, business_a_customer.id)

    def test_business_a_can_read_their_own_customer(self, business_a, business_a_customer):
        found = OrderBookService.get_customer(business_a.id, business_a_customer.id)
        assert found.id == business_a_customer.id


class TestStatusTransitions:
    """Not ownership, but the other structural guarantee this feature
    depends on: a cancelled/completed order can never be re-completed
    or re-cancelled, by anyone, including its real owner."""

    def test_cannot_complete_an_already_cancelled_order(self, business_a, business_a_order):
        OrderBookService.cancel_order(business_a.id, business_a_order.id)
        with pytest.raises(OrderBookInvalidTransitionError):
            OrderBookService.complete_order(business_a.id, business_a_order.id)

    def test_cannot_cancel_an_already_completed_order(self, business_a, business_a_order):
        OrderBookService.complete_order(business_a.id, business_a_order.id)
        with pytest.raises(OrderBookInvalidTransitionError):
            OrderBookService.cancel_order(business_a.id, business_a_order.id)
