"""
Letting an order finish.

Until now nothing moved an order out of CONFIRMED: a shop ordered, a
supplier accepted, stock changed hands in the real world, and the
record sat there forever. "Open orders" meant "every order ever
accepted", and no dispute could rest on anything because there was no
moment the platform recognised as finished.

WHAT THESE DEFEND, worst consequence first:

  A SYSTEM COMPLETION IS NEVER A BUSINESS ONE. completed_by exists for
  exactly this. "Nobody objected in time" and "the shopkeeper says it
  arrived" are different facts, and collapsing them destroys the only
  distinction that matters when somebody says the stock never came.

  DISPATCH IS OPTIONAL AND THE FLOW MUST NOT NEED IT. Most informal
  suppliers will never tap it. If confirming receipt required dispatch
  first, a supplier who taps nothing could block their own customer
  from closing their own order.

  ONLY THE BUSINESS CONFIRMS RECEIPT. The supplier is already paid on
  the digital rail, completion flatters their statistics, and nobody
  is checking.

  A COMPLETED ORDER IS STILL A SALE. Everything that counts trade reads
  TRADED_STATUSES; the architecture test holds the rule, and this holds
  the behaviour.
"""
from __future__ import annotations

import pytest

from src.domains.network.orders.errors import (
    OrderNotCompletableError,
    OrderNotDispatchableError,
    OrderNotFoundError,
)
from src.domains.network.orders.models.stock_order import (
    StockOrderCompletedBy,
    StockOrderStatus,
)
from src.domains.network.orders.repositories.stock_order_repository import (
    StockOrderRepository,
)
from src.domains.network.orders.services import fulfilment_service
from src.extensions import db


@pytest.fixture()
def confirmed_order(app, make_business, make_supplier, make_supplier_profile):
    """A real confirmed order, built the way checkout builds one."""
    from src.core.base_model import utcnow
    from src.domains.network.orders.models.stock_order import StockOrder, StockOrderItem
    from src.domains.supplier.inventory.repositories.inventory_repository import (
        InventoryRepository,
    )
    from src.domains.supplier.products.models.supplier_offer import (
        ProductCategory,
        ProductUnit,
    )
    from src.domains.supplier.products.repositories.supplier_offer_repository import (
        SupplierOfferRepository,
    )

    business = make_business()
    supplier = make_supplier()
    profile = make_supplier_profile(supplier, business_name="Fulfil Wholesale")

    product = SupplierOfferRepository.create(
        profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH,
        sku="SKU-FUL-1", product_code="PC-FUL-1",
    )
    inventory = InventoryRepository.get_or_create_for_product(product.id, profile.id)
    InventoryRepository.adjust_quantity(inventory, 50)

    order = StockOrder(
        business_id=business.id,
        supplier_profile_id=profile.id,
        status=StockOrderStatus.CONFIRMED,
        submitted_at=utcnow(),
        total_cents=2000,
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(
        StockOrderItem(
            stock_order_id=order.id, product_id=product.id,
            quantity=2, price_cents_at_add_time=1000,
        )
    )
    db.session.commit()
    return business, profile, order


class TestTheBusinessClosesTheOrder:
    def test_confirming_receipt_completes_it(self, confirmed_order):
        business, profile, order = confirmed_order

        result = fulfilment_service.confirm_received(business.id, profile.id, order.id)

        assert result["status"] == "COMPLETED"
        db.session.refresh(order)
        assert order.completed_at is not None

    def test_it_records_that_the_BUSINESS_said_so(self, confirmed_order):
        """THE FIELD THE WHOLE FEATURE EXISTS FOR. A timeout will one
        day close orders as SYSTEM, and that means "nobody objected" --
        not "it arrived". If these two ever become the same value, a
        dispute has nothing to stand on."""
        business, profile, order = confirmed_order

        fulfilment_service.confirm_received(business.id, profile.id, order.id)

        db.session.refresh(order)
        assert order.completed_by is StockOrderCompletedBy.BUSINESS
        assert order.completed_by is not StockOrderCompletedBy.SYSTEM

    def test_confirming_twice_is_refused_kindly(self, confirmed_order):
        """THE LIKELIEST CAUSE IS A DOUBLE TAP, on a slow connection, by
        somebody holding a box."""
        business, profile, order = confirmed_order
        fulfilment_service.confirm_received(business.id, profile.id, order.id)

        with pytest.raises(OrderNotCompletableError):
            fulfilment_service.confirm_received(business.id, profile.id, order.id)

    def test_another_business_cannot_close_it(
        self, confirmed_order, make_business
    ):
        """Scoped by business AND supplier, so an order id alone is
        never enough to touch somebody else's trade."""
        _, profile, order = confirmed_order
        stranger = make_business("stranger@example.com")

        with pytest.raises(OrderNotFoundError):
            fulfilment_service.confirm_received(stranger.id, profile.id, order.id)


class TestDispatchIsOptional:
    def test_an_order_can_complete_without_ever_being_dispatched(
        self, confirmed_order
    ):
        """THE ORDINARY PATH, not a degraded one. Most informal
        suppliers will never tap dispatch, and requiring it would let a
        supplier who taps nothing block their customer from closing
        their own order."""
        business, profile, order = confirmed_order

        result = fulfilment_service.confirm_received(business.id, profile.id, order.id)

        assert result["status"] == "COMPLETED"
        db.session.refresh(order)
        assert order.dispatched_at is None

    def test_a_dispatched_order_can_still_be_completed(self, confirmed_order):
        business, profile, order = confirmed_order
        fulfilment_service.mark_dispatched(profile.id, order.id)

        result = fulfilment_service.confirm_received(business.id, profile.id, order.id)

        assert result["status"] == "COMPLETED"

    def test_dispatching_twice_is_refused(self, confirmed_order):
        _, profile, order = confirmed_order
        fulfilment_service.mark_dispatched(profile.id, order.id)

        with pytest.raises(OrderNotDispatchableError):
            fulfilment_service.mark_dispatched(profile.id, order.id)

    def test_a_completed_order_cannot_be_dispatched(self, confirmed_order):
        """Stock cannot leave after it has already arrived."""
        business, profile, order = confirmed_order
        fulfilment_service.confirm_received(business.id, profile.id, order.id)

        with pytest.raises(OrderNotDispatchableError):
            fulfilment_service.mark_dispatched(profile.id, order.id)


class TestACompletedOrderIsStillASale:
    def test_it_still_counts_toward_what_the_shop_has_bought(self, confirmed_order):
        """THE SILENT FAILURE V2_14 WARNED ABOUT. Every sales total and
        trust statistic used to read status == CONFIRMED and mean "a
        real sale". If this regresses, a supplier's figures shrink as
        their orders succeed -- with no error anywhere."""
        business, profile, order = confirmed_order

        before = StockOrderRepository.previously_ordered_product_ids_for_business(
            business.id
        )
        fulfilment_service.confirm_received(business.id, profile.id, order.id)
        after = StockOrderRepository.previously_ordered_product_ids_for_business(
            business.id
        )

        assert before, "the fixture should already look like a purchase"
        assert after == before, "completing an order must not erase it from history"

    def test_it_still_counts_toward_the_buyer_count(self, confirmed_order):
        business, profile, order = confirmed_order
        product_id = order.items[0].product_id

        fulfilment_service.confirm_received(business.id, profile.id, order.id)

        counts = StockOrderRepository.buyer_counts_for_products([product_id])
        assert counts.get(product_id) == 1

    def test_it_stays_in_the_shop_own_order_history(self, confirmed_order):
        business, profile, order = confirmed_order

        fulfilment_service.confirm_received(business.id, profile.id, order.id)

        history = StockOrderRepository.list_submitted_for_business_and_supplier(
            business.id, profile.id
        )
        assert order.id in [o.id for o in history]
