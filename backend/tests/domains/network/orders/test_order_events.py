"""
The order's own history (V2_13 §3.2).

WHAT THIS DEFENDS. stock_orders carried only its CURRENT status, so
"why did this order change, and who changed it?" was answerable by
inference at best -- and that is a support question that exists today,
not a hypothetical one.

THE SHARPEST CASE IS CANCELLATION. A business cancelling and a
supplier cancelling produce the IDENTICAL status, so the status column
cannot tell them apart. Which side walked away is the first thing
anybody asks. test_the_two_cancellations_are_distinguishable is the
one that would fail if somebody collapsed the event types back into
the status.

AND THE TRANSITION MATTERS, NOT JUST THE DESTINATION. "Cancelled from
PENDING_SUPPLIER_APPROVAL" and "cancelled from CONFIRMED" are
different events commercially -- the second cancels a trade the
supplier had already agreed to.

Events are written INSIDE the caller's transaction, so these tests
also prove the history and the state land together rather than the
log being a best-effort side effect.
"""
from __future__ import annotations

from itertools import count

import pytest

from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
from src.domains.network.orders.models.stock_order import StockOrderStatus
from src.domains.network.orders.models.stock_order_event import (
    StockOrderEventActor,
    StockOrderEventType,
)
from src.domains.network.orders.services import (
    cancellation_service,
    cart_service,
    checkout_service,
    order_event_service,
)
from src.domains.supplier.products.services import product_service
from src.domains.supplier.stock_order_management.services import order_management_service
from src.extensions import db


def _product(profile_id, name="Bread"):
    """A product WITH STOCK. add_item refuses an out-of-stock product,
    so a bare create_product cannot be added to a cart -- same helper
    shape as test_cart_and_checkout.py's own _make_product."""
    from src.domains.supplier.inventory.repositories.inventory_repository import (
        InventoryRepository,
    )

    product = product_service.create_product(
        supplier_profile_id=profile_id,
        name=name,
        category=ProductCategory.OTHER,
        price_cents=1000,
        selling_unit=ProductUnit.EACH,
    )
    inventory = InventoryRepository.get_or_create_for_product(product.id, profile_id)
    InventoryRepository.adjust_quantity(inventory, 100)
    return product


@pytest.fixture()
def placed(make_business, make_supplier, make_supplier_profile, make_active_connection):
    """A real order, placed through the real checkout."""

    # UNIQUE EMAILS PER CALL. The factories default to one address
    # each, so a test that places TWO orders collides on the users
    # email unique index -- which surfaces as an IntegrityError deep in
    # a fixture and reads like a database problem rather than a
    # duplicate default.
    seq = count()

    def _make(business_name="Events Co"):
        n = next(seq)
        business = make_business(f"buyer{n}@example.com")
        supplier_user = make_supplier(f"seller{n}@example.com")
        profile = make_supplier_profile(supplier_user, business_name=business_name)
        make_active_connection(business, profile)
        product = _product(profile.id)
        cart_service.add_item(business.id, profile.id, product.id, 2)
        result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "COLLECT")

        from src.domains.network.orders.repositories.stock_order_repository import (
            StockOrderRepository,
        )

        order = StockOrderRepository.get_by_id(result["id"])
        return business, supplier_user, profile, order

    return _make


def _events(order):
    return order_event_service.list_for_order(order.id)


class TestPlacing:
    def test_placing_writes_the_first_event(self, app, db_session, placed):
        _, _, _, order = placed()

        events = _events(order)

        assert len(events) == 1
        assert events[0].event_type == StockOrderEventType.PLACED
        assert events[0].actor == StockOrderEventActor.BUSINESS
        assert events[0].to_status == StockOrderStatus.PENDING_SUPPLIER_APPROVAL

    def test_the_first_event_comes_from_the_cart(self, app, db_session, placed):
        """from_status is CART exactly once per order, and it is the one
        row where the previous state is worth naming."""
        _, _, _, order = placed()

        assert _events(order)[0].from_status == StockOrderStatus.CART

    def test_both_parties_are_on_the_row(self, app, db_session, placed):
        """Denormalised so either side reads their own history without
        joining back through stock_orders -- and so a webhook
        dispatcher knows who to deliver to without a lookup."""
        business, _, profile, order = placed()

        event = _events(order)[0]
        assert str(event.business_id) == str(business.id)
        assert str(event.supplier_profile_id) == str(profile.id)


class TestDeciding:
    def test_confirming_appends_rather_than_replacing(self, app, db_session, placed):
        """APPEND-ONLY. The placement event survives the confirmation --
        a history that overwrote itself would answer nothing."""
        _, _, profile, order = placed()

        order_management_service.approve_order(profile.id, order.id)

        events = _events(order)
        assert [e.event_type for e in events] == [
            StockOrderEventType.PLACED,
            StockOrderEventType.CONFIRMED,
        ]
        assert events[1].from_status == StockOrderStatus.PENDING_SUPPLIER_APPROVAL
        assert events[1].to_status == StockOrderStatus.CONFIRMED

    def test_declining_keeps_the_reason(self, app, db_session, placed):
        """The reason is the most useful column on the table when
        somebody is asking what went wrong."""
        _, _, profile, order = placed()

        order_management_service.decline_order(
            profile.id, order.id, reason="out_of_stock", details="No bread until Thursday"
        )

        last = _events(order)[-1]
        assert last.event_type == StockOrderEventType.DECLINED
        assert last.actor == StockOrderEventActor.SUPPLIER
        assert last.reason == "No bread until Thursday"


class TestCancellation:
    def test_the_two_cancellations_are_distinguishable(
        self, app, db_session, placed
    ):
        """THE TEST THAT JUSTIFIES THE EVENT TYPE EXISTING AT ALL.

        Both paths set status = CANCELLED. If the log recorded only the
        status, the record could not say which side walked away -- which
        is the first thing anybody asks about a cancelled order.
        """
        business_a, _, profile_a, order_a = placed("Business Cancels")
        _, _, profile_b, order_b = placed("Supplier Cancels")

        cancellation_service.cancel_order_by_business(
            business_a.id, profile_a.id, order_a.id, reason="changed_mind", details=None
        )
        order_management_service.approve_order(profile_b.id, order_b.id)
        order_management_service.cancel_order(
            profile_b.id, order_b.id, reason="out_of_stock", details=None
        )

        assert _events(order_a)[-1].event_type == StockOrderEventType.CANCELLED_BY_BUSINESS
        assert _events(order_b)[-1].event_type == StockOrderEventType.CANCELLED_BY_SUPPLIER
        # Same destination, different stories.
        assert _events(order_a)[-1].to_status == _events(order_b)[-1].to_status

    def test_cancelling_a_confirmed_order_records_where_it_came_from(
        self, app, db_session, placed
    ):
        """"Cancelled from CONFIRMED" is commercially different from
        "cancelled from PENDING" -- the supplier had already agreed."""
        _, _, profile, order = placed()

        order_management_service.approve_order(profile.id, order.id)
        order_management_service.cancel_order(
            profile.id, order.id, reason="out_of_stock", details=None
        )

        assert _events(order)[-1].from_status == StockOrderStatus.CONFIRMED


def test_the_history_is_append_only_by_construction(app):
    """StockOrderEvent is a plain db.Model, not BaseModel -- so it has
    no is_deleted to soft-delete a row out of the record. A history you
    can quietly remove entries from is not a history."""
    from src.domains.network.orders.models.stock_order_event import StockOrderEvent

    assert not hasattr(StockOrderEvent, "is_deleted")
    assert not hasattr(StockOrderEvent, "deleted_at")
