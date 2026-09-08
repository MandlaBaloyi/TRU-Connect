"""
Formal, permanent test coverage for domains/business/stock_order and
the shared/checkout infrastructure it depends on. Converts the direct
verification scripts run during development into real pytest
regression protection. See each service module's own docstrings for
the full reasoning behind what's being tested here.
"""
from __future__ import annotations

import threading
import uuid

import pytest

from src.domains.network.orders.services.commission import calculate_platform_commission_cents
from src.domains.business.order_limits.tiers.free import LIMITS as FREE_LIMITS
from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.domains.supplier.products.services import product_service
from src.extensions import db
from src.domains.network.orders.errors import (
    CartItemNotFoundError,
    CartNotFoundError,
    EmptyCartError,
    OutOfStockError,
    InvalidQuantityError,
    OrderLimitExceededError,
    OrderNotCancellableError,
    OrderNotFoundError,
    PaymentMethodNotAvailableError,
    ProductNotFoundError,
    StaleCartItemError,
    SupplierNotConnectedError,
    SupplierNotFoundError,
)
from src.domains.network.orders.services import cancellation_service, cart_service, checkout_service, order_history_service
from src.domains.network.orders.models.stock_order import (
    StockOrder,
    StockOrderCancelReason,
    StockOrderDeclineReason,
    StockOrderPaymentMethod,
    StockOrderStatus,
)
from src.domains.supplier.stock_order_management.services import order_management_service
from src.domains.network.orders.models.stock_order_payment import StockOrderPayment, StockOrderPaymentStatus
from src.domains.network.orders.providers.composition import get_payment_provider, reset_payment_providers
from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository


def _make_product(profile_id, name="Product", category=ProductCategory.OTHER, price_cents=1000, selling_unit=ProductUnit.EACH, in_stock=True):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    product = SupplierOfferRepository.create(
        profile_id, name, category, price_cents, selling_unit,
        sku=generate_sku(profile_id), product_code=generate_product_code(),
    )
    if in_stock:
        inventory = InventoryRepository.get_or_create_for_product(product.id, profile_id)
        InventoryRepository.adjust_quantity(inventory, 100)
    return product


# --- get_or_create_cart: the real concurrency guarantee --------------------


def test_get_or_create_cart_ten_concurrent_callers_converge_on_one_row(
    app, make_business, make_supplier, make_supplier_profile
):
    """THE MOST IMPORTANT GUARANTEE IN THIS WHOLE DESIGN, proven with
    genuinely concurrent threads and independent database sessions --
    not just trusted from the logic on paper."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Concurrency Co")
    business_id, profile_id = business.id, profile.id

    results = []
    errors = []
    barrier = threading.Barrier(10)

    def worker():
        with app.app_context():
            try:
                barrier.wait()
                cart = StockOrderRepository.get_or_create_cart(business_id, profile_id)
                results.append(cart.id)
            except Exception as e:
                errors.append(repr(e))
            finally:
                db.session.remove()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"threads raised: {errors}"
    assert len(set(results)) == 1, f"threads converged on {len(set(results))} different carts, not 1"

    real_count = StockOrder.query.filter_by(business_id=business_id, supplier_profile_id=profile_id).count()
    assert real_count == 1, f"{real_count} rows actually exist, not 1"


# --- cart_service ------------------------------------------------------


def test_add_item_creates_cart_and_item(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Add Item Co")
    bread = _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000)

    cart = cart_service.add_item(business.id, profile.id, bread.id, 2)

    assert cart["itemCount"] == 1
    assert cart["items"][0]["quantity"] == 2
    assert cart["items"][0]["priceCentsAtAddTime"] == 1000
    assert cart["totalCents"] == 2000


def test_add_item_twice_increments_not_duplicates(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Increment Co")
    bread = _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000)

    cart_service.add_item(business.id, profile.id, bread.id, 2)
    cart = cart_service.add_item(business.id, profile.id, bread.id, 3)

    assert cart["itemCount"] == 1
    assert cart["items"][0]["quantity"] == 5
    assert cart["totalCents"] == 5000


def test_price_snapshot_is_unaffected_by_a_later_price_change(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Price Snapshot Co")
    bread = _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000)
    cart_service.add_item(business.id, profile.id, bread.id, 2)

    product_service.update_product(
        bread.id, profile.id, name="Bread", category=ProductCategory.BAKERY, price_cents=99999, selling_unit=ProductUnit.EACH
    )

    cart = cart_service.get_cart(business.id, profile.id)
    assert cart["items"][0]["priceCentsAtAddTime"] == 1000
    assert cart["totalCents"] == 2000


def test_add_item_rejects_a_different_suppliers_product(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    owner = make_supplier("cart-owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Owner Co")
    other = make_supplier("cart-other@example.com")
    other_profile = make_supplier_profile(other, business_name="Other Co")
    other_product = _make_product(other_profile.id, "Not Theirs")

    with pytest.raises(ProductNotFoundError):
        cart_service.add_item(business.id, owner_profile.id, other_product.id, 1)


def test_add_item_rejects_an_archived_product(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Archived Reject Co")
    product = _make_product(profile.id, "Milk")
    product_service.archive_product(product.id, profile.id)

    with pytest.raises(ProductNotFoundError):
        cart_service.add_item(business.id, profile.id, product.id, 1)


def test_add_item_rejects_a_quantity_below_one(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Qty Co")
    product = _make_product(profile.id, "Bread")

    with pytest.raises(InvalidQuantityError):
        cart_service.add_item(business.id, profile.id, product.id, 0)


def test_update_item_quantity_recalculates_total(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Update Qty Co")
    product = _make_product(profile.id, "Milk", price_cents=1500)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    cart = cart_service.update_item_quantity(business.id, profile.id, product.id, 4)

    assert cart["totalCents"] == 1500 * 4


def test_update_item_quantity_raises_for_no_cart(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Cart Co")
    product = _make_product(profile.id, "Milk")

    with pytest.raises(CartNotFoundError):
        cart_service.update_item_quantity(business.id, profile.id, product.id, 2)


def test_update_item_quantity_raises_for_item_not_in_cart(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Item Not In Cart Co")
    bread = _make_product(profile.id, "Bread")
    milk = _make_product(profile.id, "Milk")
    cart_service.add_item(business.id, profile.id, bread.id, 1)

    with pytest.raises(CartItemNotFoundError):
        cart_service.update_item_quantity(business.id, profile.id, milk.id, 2)


def test_remove_item_recalculates_total(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Remove Co")
    bread = _make_product(profile.id, "Bread", price_cents=1000)
    milk = _make_product(profile.id, "Milk", price_cents=1500)
    cart_service.add_item(business.id, profile.id, bread.id, 2)
    cart_service.add_item(business.id, profile.id, milk.id, 1)

    cart = cart_service.remove_item(business.id, profile.id, milk.id)

    assert cart["itemCount"] == 1
    assert cart["totalCents"] == 2000


def test_get_cart_returns_none_when_nothing_exists(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Empty Co")

    assert cart_service.get_cart(business.id, profile.id) is None


def test_list_my_carts_returns_every_supplier_with_an_incomplete_cart(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_a = make_supplier("list-carts-a@example.com")
    profile_a = make_supplier_profile(supplier_a, business_name="List Carts A")
    supplier_b = make_supplier("list-carts-b@example.com")
    profile_b = make_supplier_profile(supplier_b, business_name="List Carts B")
    product_a = _make_product(profile_a.id, "A Product")
    product_b = _make_product(profile_b.id, "B Product")

    cart_service.add_item(business.id, profile_a.id, product_a.id, 1)
    cart_service.add_item(business.id, profile_b.id, product_b.id, 1)

    carts = cart_service.list_my_carts(business.id)

    assert {c["supplierName"] for c in carts} == {"List Carts A", "List Carts B"}


# --- checkout_service: core flow ------------------------------------------


def test_submit_checkout_with_no_cart_raises(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Cart Checkout Co")
    make_active_connection(business, profile)

    with pytest.raises(CartNotFoundError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")


def test_submit_checkout_rejects_payfast_as_not_yet_available(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Payfast Reject Co")
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    with pytest.raises(PaymentMethodNotAvailableError):
        checkout_service.submit_checkout(business.id, profile.id, "PAYFAST", "DELIVER")


def test_submit_checkout_succeeds_with_cash(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Cash Checkout Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 2)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "COLLECT")

    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"
    assert result["totalCents"] == 2000
    assert result["instructions"] is not None
    # THE REAL GAP FOUND AND FIXED: the reference must be present in
    # the IMMEDIATE checkout response -- Order Placed needs to show it
    # right away, not only once a business later checks history.
    assert result["orderReference"] is not None
    assert result["orderReference"].startswith("TRU-")


def test_submit_checkout_succeeds_with_proof_of_payment(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="POP Checkout Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "PROOF_OF_PAYMENT", "DELIVER")

    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


def test_submit_checkout_leaves_no_active_cart_behind(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Active After Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert cart_service.get_cart(business.id, profile.id) is None


def test_cannot_resubmit_an_already_submitted_order(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Resubmit Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    with pytest.raises(CartNotFoundError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")


def test_submit_checkout_rejects_an_empty_cart(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Empty Checkout Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    cart_service.remove_item(business.id, profile.id, product.id)

    with pytest.raises(EmptyCartError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")


def test_submit_checkout_rejects_a_stale_archived_item_and_names_it(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Stale Item Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Milk")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    product_service.archive_product(product.id, profile.id)

    with pytest.raises(StaleCartItemError) as exc_info:
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert str(product.id) in exc_info.value.data["staleProductIds"]


def test_submit_checkout_raises_for_a_genuinely_nonexistent_supplier(make_business):
    business = make_business()

    with pytest.raises(SupplierNotFoundError):
        checkout_service.submit_checkout(business.id, uuid.uuid4(), "CASH", "DELIVER")


def test_submit_checkout_creates_a_real_payment_record(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Payment Record Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Item", price_cents=10000)
    cart_service.add_item(business.id, profile.id, product.id, 2)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    payment = StockOrderPayment.query.filter_by(stock_order_id=result["id"]).first()
    assert payment is not None
    # DUE, NOT SUCCEEDED. This assertion used to be the opposite, and
    # it was locking in a false claim: nobody has handed over cash at
    # the moment an order is submitted. See StockOrderPaymentStatus.
    assert payment.status == StockOrderPaymentStatus.DUE
    assert payment.payment_method == "CASH"
    assert payment.amount_cents == 20000
    assert payment.platform_commission_cents == 0
    # No completion date either -- nothing has completed. A cash
    # payment gets one when someone who was there confirms it.
    assert payment.completed_at is None


# --- provider isolation ---------------------------------------------------


def test_manual_checkout_works_with_zero_payfast_config(monkeypatch):
    for var in ["PAYFAST_MERCHANT_ID", "PAYFAST_MERCHANT_KEY", "PAYFAST_PASSPHRASE"]:
        monkeypatch.delenv(var, raising=False)
    reset_payment_providers()

    cash_provider = get_payment_provider(StockOrderPaymentMethod.CASH)
    outcome = cash_provider.process_checkout(stock_order=None, payment_method=StockOrderPaymentMethod.CASH)
    assert outcome.order_status == StockOrderStatus.PENDING_SUPPLIER_APPROVAL
    assert outcome.instructions is not None

    pop_provider = get_payment_provider(StockOrderPaymentMethod.PROOF_OF_PAYMENT)
    outcome = pop_provider.process_checkout(stock_order=None, payment_method=StockOrderPaymentMethod.PROOF_OF_PAYMENT)
    assert outcome.order_status == StockOrderStatus.PENDING_SUPPLIER_APPROVAL


def test_payfast_provider_raises_not_implemented(monkeypatch):
    reset_payment_providers()
    provider = get_payment_provider(StockOrderPaymentMethod.PAYFAST)

    with pytest.raises(NotImplementedError):
        provider.process_checkout(stock_order=None, payment_method=StockOrderPaymentMethod.PAYFAST)


# --- commission calculation -------------------------------------------


@pytest.mark.parametrize(
    "order_total_cents,expected_commission_cents",
    [
        (0, 0),
        (49900, 0),
        (50000, 500),
        (99900, 500),
        (100000, 1000),
        (149900, 1000),
        (150000, 1500),
    ],
)
def test_calculate_platform_commission_cents_for_payfast(order_total_cents, expected_commission_cents):
    result = calculate_platform_commission_cents(order_total_cents, StockOrderPaymentMethod.PAYFAST)
    assert result == expected_commission_cents


def test_calculate_platform_commission_cents_is_zero_for_cash():
    assert calculate_platform_commission_cents(1_000_000, StockOrderPaymentMethod.CASH) == 0


def test_calculate_platform_commission_cents_is_zero_for_proof_of_payment():
    assert calculate_platform_commission_cents(1_000_000, StockOrderPaymentMethod.PROOF_OF_PAYMENT) == 0


# --- tier-aware spending limits --------------------------------------------
#
# FREE tier is the only one reachable today (get_current_tier always
# returns FREE -- see domains/business/tiers/resolver.py's own
# docstring on why). These tests exercise the REAL, live values from
# tiers/free.py directly, not hardcoded numbers duplicated here --
# if free.py's own numbers ever change, these tests stay correct
# without needing to change too.


def test_cash_order_within_the_per_transaction_cap_succeeds(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Within Cash Cap Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Item", price_cents=FREE_LIMITS.direct_transaction_cap_cents)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


def test_cash_order_over_the_per_transaction_cap_is_rejected(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Over Cash Cap Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Item", price_cents=FREE_LIMITS.direct_transaction_cap_cents + 1)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    with pytest.raises(OrderLimitExceededError) as exc_info:
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert exc_info.value.data["reason"] == "PER_TRANSACTION_LIMIT"
    assert exc_info.value.data["limitCents"] == FREE_LIMITS.direct_transaction_cap_cents


def test_direct_rail_has_one_cap_regardless_of_which_legacy_method_is_sent(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE DIFFERENTIATION IS GONE, ON PURPOSE, and this test now
    proves its absence rather than its presence.

    It used to assert that proof-of-payment earned a higher
    per-transaction cap than cash. That cap difference was never
    enforceable: nothing stopped a buyer picking proof-of-payment to
    get the higher ceiling and then handing over notes, so it was a
    real limit resting on an unverifiable self-declaration. Both are
    now the one DIRECT rail with one cap -- see
    StockOrderPaymentMethod.

    Kept rather than deleted because the loophole is worth a permanent
    guard: if someone ever reintroduces a per-method cap, this fails.
    """
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Same Cap Either Way Co")
    make_active_connection(business, profile)

    over_the_cap = FREE_LIMITS.direct_transaction_cap_cents + 1
    product = _make_product(profile.id, "Item", price_cents=over_the_cap)

    # The historical value must not buy a bigger order than the current
    # one does. Both are the same rail now.
    for method in ("PROOF_OF_PAYMENT", "CASH", "DIRECT"):
        cart_service.add_item(business.id, profile.id, product.id, 1)
        with pytest.raises(OrderLimitExceededError) as exc_info:
            checkout_service.submit_checkout(business.id, profile.id, method, "DELIVER")
        assert exc_info.value.data["reason"] == "PER_TRANSACTION_LIMIT"
        assert exc_info.value.data["limitCents"] == FREE_LIMITS.direct_transaction_cap_cents


def test_monthly_cumulative_cap_is_enforced_across_multiple_separate_orders(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL LOOPHOLE FIX, proven directly -- confirmed after
    review that a per-transaction cap alone can be defeated by simply
    placing several smaller orders instead of one large one. This
    proves the cumulative check catches that pattern across genuinely
    separate submit_checkout calls, not just within one."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Monthly Cumulative Co")
    make_active_connection(business, profile)
    # Each order individually under BOTH per-transaction caps, but
    # together they exceed the monthly cap.
    per_order_cents = FREE_LIMITS.direct_transaction_cap_cents
    orders_to_hit_cap = FREE_LIMITS.monthly_manual_payment_cap_cents // per_order_cents

    product = _make_product(profile.id, "Item", price_cents=per_order_cents)
    for _ in range(orders_to_hit_cap):
        cart_service.add_item(business.id, profile.id, product.id, 1)
        result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
        assert result["status"] == "PENDING_SUPPLIER_APPROVAL"

    # One more, individually still within the per-transaction cap, must
    # now be rejected on the CUMULATIVE total.
    cart_service.add_item(business.id, profile.id, product.id, 1)
    with pytest.raises(OrderLimitExceededError) as exc_info:
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert exc_info.value.data["reason"] == "MONTHLY_CUMULATIVE_LIMIT"
    assert exc_info.value.data["alreadySpentThisMonthCents"] == orders_to_hit_cap * per_order_cents


def _fill_month_to_cap(business, profile, product, per_order_cents):
    """Submit exactly enough CASH orders to consume the whole monthly
    manual-payment cap. Returns the submitted orders."""
    orders = []
    for _ in range(FREE_LIMITS.monthly_manual_payment_cap_cents // per_order_cents):
        cart_service.add_item(business.id, profile.id, product.id, 1)
        orders.append(checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER"))
    return orders


def test_a_declined_order_gives_its_monthly_spend_back(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL BUG, reported directly: spend the whole monthly cap,
    have the supplier DECLINE one of those orders, and the business was
    still locked out -- the declined order kept consuming the cap for
    the rest of the month.

    The cause was that a CASH / PROOF_OF_PAYMENT payment row is written
    SUCCEEDED at SUBMISSION, before the supplier has even seen the
    order, and the monthly sum filtered on the PAYMENT's status without
    ever looking at the ORDER's. A supplier's refusal moves no money,
    so it must not consume a limit whose whole purpose is to bound how
    much unverified money a business actually moves.
    """
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Declined Releases Co")
    make_active_connection(business, profile)

    per_order_cents = FREE_LIMITS.direct_transaction_cap_cents
    product = _make_product(profile.id, "Item", price_cents=per_order_cents)
    orders = _fill_month_to_cap(business, profile, product, per_order_cents)

    # At the cap: the next order is refused.
    cart_service.add_item(business.id, profile.id, product.id, 1)
    with pytest.raises(OrderLimitExceededError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    # The supplier declines one. That money never changed hands.
    order_management_service.decline_order(
        profile.id, orders[0]["id"], StockOrderDeclineReason.OUT_OF_STOCK.value
    )

    # The same order now goes through, because the headroom came back.
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


def test_a_supplier_cancelled_order_gives_its_monthly_spend_back(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """The other half of the same bug: an order the supplier APPROVED
    and then cancelled is just as much money that never moved."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Cancelled Releases Co")
    make_active_connection(business, profile)

    per_order_cents = FREE_LIMITS.direct_transaction_cap_cents
    product = _make_product(profile.id, "Item", price_cents=per_order_cents)
    orders = _fill_month_to_cap(business, profile, product, per_order_cents)

    order_management_service.approve_order(profile.id, orders[0]["id"])
    order_management_service.cancel_order(
        profile.id, orders[0]["id"], StockOrderCancelReason.OUT_OF_STOCK.value
    )

    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


def test_a_business_cancelled_order_gives_its_monthly_spend_back(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """And the third path into CANCELLED -- the business pulling out of
    its own still-pending order."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Business Cancel Releases Co")
    make_active_connection(business, profile)

    per_order_cents = FREE_LIMITS.direct_transaction_cap_cents
    product = _make_product(profile.id, "Item", price_cents=per_order_cents)
    orders = _fill_month_to_cap(business, profile, product, per_order_cents)

    cancellation_service.cancel_order_by_business(
        business.id, profile.id, orders[0]["id"], StockOrderCancelReason.CHANGED_MIND.value
    )

    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


def test_a_pending_order_still_consumes_the_monthly_cap(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE OTHER DIRECTION, and the reason the fix excludes two dead
    statuses rather than counting only CONFIRMED ones. An order
    awaiting the supplier's decision must still count: if it did not, a
    business could fire off unlimited orders in parallel, each one
    individually passing the check because none of the others had been
    approved yet, and the cumulative cap would mean nothing at all.
    """
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Pending Still Counts Co")
    make_active_connection(business, profile)

    per_order_cents = FREE_LIMITS.direct_transaction_cap_cents
    product = _make_product(profile.id, "Item", price_cents=per_order_cents)
    orders = _fill_month_to_cap(business, profile, product, per_order_cents)

    # Every one of them is still PENDING_SUPPLIER_APPROVAL -- nothing
    # has been approved, declined or cancelled.
    assert all(order["status"] == "PENDING_SUPPLIER_APPROVAL" for order in orders)

    cart_service.add_item(business.id, profile.id, product.id, 1)
    with pytest.raises(OrderLimitExceededError) as exc_info:
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    assert exc_info.value.data["reason"] == "MONTHLY_CUMULATIVE_LIMIT"


def test_an_approved_order_still_consumes_the_monthly_cap(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """A CONFIRMED order is real spending and must keep counting -- the
    fix must not release anything beyond the two dead states."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Approved Still Counts Co")
    make_active_connection(business, profile)

    per_order_cents = FREE_LIMITS.direct_transaction_cap_cents
    product = _make_product(profile.id, "Item", price_cents=per_order_cents)
    orders = _fill_month_to_cap(business, profile, product, per_order_cents)

    for order in orders:
        order_management_service.approve_order(profile.id, order["id"])

    cart_service.add_item(business.id, profile.id, product.id, 1)
    with pytest.raises(OrderLimitExceededError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")


def test_monthly_cumulative_cap_is_shared_across_cash_and_proof_of_payment(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE SECOND HALF OF THE SAME LOOPHOLE FIX -- switching payment
    METHOD between orders must not reset the running total either."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Shared Cap Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Item", price_cents=FREE_LIMITS.direct_transaction_cap_cents)

    cart_service.add_item(business.id, profile.id, product.id, 1)
    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    remaining = FREE_LIMITS.monthly_manual_payment_cap_cents - FREE_LIMITS.direct_transaction_cap_cents
    if remaining < FREE_LIMITS.direct_transaction_cap_cents:
        # Not enough room left for another full cash-cap order --
        # confirm the SAME running total is visible from the POP side.
        cart_service.add_item(business.id, profile.id, product.id, 1)
        with pytest.raises(OrderLimitExceededError) as exc_info:
            checkout_service.submit_checkout(business.id, profile.id, "PROOF_OF_PAYMENT", "DELIVER")
        assert exc_info.value.data["alreadySpentThisMonthCents"] == FREE_LIMITS.direct_transaction_cap_cents


def test_order_at_exactly_the_per_transaction_cap_is_allowed(make_business, make_supplier, make_supplier_profile, make_active_connection):
    """The cap is inclusive -- exactly at it succeeds, only strictly
    over it is rejected."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Exactly At Cap Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Item", price_cents=FREE_LIMITS.direct_transaction_cap_cents)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


# --- out-of-stock rejection (real bug found and fixed) ---------------------


def test_add_item_rejects_an_out_of_stock_product(make_business, make_supplier, make_supplier_profile):
    """A REAL BUG FOUND AFTER DIRECT REPORT -- this check never
    existed at all before. Confirmed here that a product with zero
    available stock is now rejected, with a clear message naming the
    exact product."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Out Of Stock Reject Co")
    product = _make_product(profile.id, "Never Stocked", in_stock=False)

    with pytest.raises(OutOfStockError) as exc_info:
        cart_service.add_item(business.id, profile.id, product.id, 1)

    assert exc_info.value.data["productId"] == str(product.id)


def test_add_item_succeeds_for_an_in_stock_product(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="In Stock Co")
    product = _make_product(profile.id, "Bread", in_stock=True)

    cart = cart_service.add_item(business.id, profile.id, product.id, 1)

    assert cart["itemCount"] == 1


# --- clear_cart ------------------------------------------------------------


def test_clear_cart_empties_every_item(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Clear Cart Co")
    bread = _make_product(profile.id, "Bread")
    milk = _make_product(profile.id, "Milk")
    cart_service.add_item(business.id, profile.id, bread.id, 2)
    cart_service.add_item(business.id, profile.id, milk.id, 1)

    cleared = cart_service.clear_cart(business.id, profile.id)

    assert cleared["itemCount"] == 0
    assert cleared["totalCents"] == 0


def test_cart_still_usable_after_clearing(make_business, make_supplier, make_supplier_profile):
    """The cart row itself stays -- clearing isn't the same as
    abandoning the supplier relationship."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Reuse After Clear Co")
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    cart_service.clear_cart(business.id, profile.id)

    cart = cart_service.add_item(business.id, profile.id, product.id, 1)

    assert cart["itemCount"] == 1


def test_clear_cart_raises_for_no_cart(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Cart Clear Co")

    with pytest.raises(CartNotFoundError):
        cart_service.clear_cart(business.id, profile.id)


# --- order_history_service --------------------------------------------


def test_order_history_is_empty_before_any_submission(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Empty History Co")

    history = order_history_service.list_order_history(business.id, profile.id)

    assert history == []


def test_order_history_shows_a_real_submitted_order(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Real History Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 2)
    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    history = order_history_service.list_order_history(business.id, profile.id)

    assert len(history) == 1
    assert history[0]["status"] == "PENDING_SUPPLIER_APPROVAL"
    assert history[0]["paymentMethod"] == "CASH"
    assert history[0]["totalCents"] == 2000
    assert history[0]["itemCount"] == 1


def test_order_history_never_includes_an_unsubmitted_cart(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Cart Not History Co")
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)  # never submitted

    history = order_history_service.list_order_history(business.id, profile.id)

    assert history == []


def test_order_history_is_scoped_to_one_supplier(make_business, make_supplier, make_supplier_profile, make_active_connection):
    """A business's order from Supplier A must never appear in
    Supplier B's own history list."""
    business = make_business()
    supplier_a = make_supplier("history-scope-a@example.com")
    profile_a = make_supplier_profile(supplier_a, business_name="History Scope A")
    make_active_connection(business, profile_a)
    supplier_b = make_supplier("history-scope-b@example.com")
    profile_b = make_supplier_profile(supplier_b, business_name="History Scope B")
    product_a = _make_product(profile_a.id, "A Product")
    cart_service.add_item(business.id, profile_a.id, product_a.id, 1)
    checkout_service.submit_checkout(business.id, profile_a.id, "CASH", "DELIVER")

    history_b = order_history_service.list_order_history(business.id, profile_b.id)

    assert history_b == []


def test_order_history_raises_for_a_genuinely_nonexistent_supplier(make_business):
    business = make_business()

    with pytest.raises(SupplierNotFoundError):
        order_history_service.list_order_history(business.id, uuid.uuid4())


# --- inventory reservation --------------------------------------------


def test_submit_checkout_reserves_real_inventory(make_business, make_supplier, make_supplier_profile, make_active_connection):
    """THE REAL WIRING of quantity_reserved, confirmed directly --
    that field existed unused since Inventory was first built, with
    its own comment saying explicitly it was waiting for exactly this
    moment."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Reservation Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    inventory = InventoryRepository.get_by_product_id(product.id)
    assert inventory.quantity_reserved == 0

    cart_service.add_item(business.id, profile.id, product.id, 4)
    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    from src.extensions import db as _db
    _db.session.expire_all()
    inventory = InventoryRepository.get_by_product_id(product.id)
    assert inventory.quantity_reserved == 4
    assert inventory.quantity_on_hand == 100  # on_hand untouched -- only reserved changes


def test_checkout_rejects_stock_consumed_between_add_and_checkout(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL, DIRECT PROOF this whole reservation system exists to
    provide: two businesses racing for the same limited stock must
    never both succeed. The second business's own add_item succeeded
    (stock was genuinely available at that moment); by the time they
    check out, the first business's own order has already reserved
    everything -- confirmed rejected, not silently oversold."""
    business_a = make_business("race-condition-a@example.com")
    business_b = make_business("race-condition-b@example.com")
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Race Condition Co")
    make_active_connection(business_a, profile)
    make_active_connection(business_b, profile)
    product = _make_product(profile.id, "Limited Stock Item", price_cents=1000, in_stock=False)
    inventory = InventoryRepository.get_or_create_for_product(product.id, profile.id)
    InventoryRepository.adjust_quantity(inventory, 5)  # only 5 available, total

    # Both businesses add while 5 is genuinely available.
    cart_service.add_item(business_a.id, profile.id, product.id, 5)
    cart_service.add_item(business_b.id, profile.id, product.id, 5)

    # A checks out first, reserving all 5.
    result_a = checkout_service.submit_checkout(business_a.id, profile.id, "CASH", "DELIVER")
    assert result_a["status"] == "PENDING_SUPPLIER_APPROVAL"

    # B's own cart still has 5 items (nothing removed it), but the
    # real stock is now fully reserved by A -- B's checkout must fail.
    with pytest.raises(StaleCartItemError) as exc_info:
        checkout_service.submit_checkout(business_b.id, profile.id, "CASH", "DELIVER")

    assert str(product.id) in exc_info.value.data["staleProductIds"]


# --- order_history_service: get_order_detail --------------------------


def test_get_order_detail_returns_full_line_item_information(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Detail Test Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 3)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    detail = order_history_service.get_order_detail(business.id, profile.id, result["id"])

    assert detail["status"] == "PENDING_SUPPLIER_APPROVAL"
    assert detail["totalCents"] == 3000
    assert len(detail["items"]) == 1
    assert detail["items"][0]["productName"] == "Bread"
    assert detail["items"][0]["quantity"] == 3


def test_get_order_detail_decline_fields_are_null_when_not_declined(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Not Declined Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    detail = order_history_service.get_order_detail(business.id, profile.id, result["id"])

    assert detail["declineReason"] is None
    assert detail["declineDetails"] is None


def test_get_order_detail_returns_real_decline_reason_and_details(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """Goes through the REAL decline_order flow, not a hand-set model
    attribute -- confirms the business's own order-detail view
    genuinely reflects a supplier's real decision, not just that the
    two fields exist on the model."""
    from src.domains.supplier.stock_order_management.services import order_management_service

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Declined Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    order_management_service.decline_order(
        profile.id, result["id"], "out_of_stock", "Sold out this week, restocking Friday."
    )

    detail = order_history_service.get_order_detail(business.id, profile.id, result["id"])

    assert detail["status"] == "DECLINED"
    assert detail["declineReason"] == "out_of_stock"
    assert detail["declineDetails"] == "Sold out this week, restocking Friday."


def test_get_order_detail_blocks_a_different_business(make_business, make_supplier, make_supplier_profile, make_active_connection):
    """THE REAL IDOR PROTECTION -- a business must never be able to
    view another business's own order, even with a genuinely valid
    order id."""
    business = make_business()
    other_business = make_business("idor-other-business@example.com")
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="IDOR Test Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    with pytest.raises(OrderNotFoundError):
        order_history_service.get_order_detail(other_business.id, profile.id, result["id"])


def test_get_order_detail_raises_for_a_genuinely_nonexistent_order(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Nonexistent Order Co")

    with pytest.raises(OrderNotFoundError):
        order_history_service.get_order_detail(business.id, profile.id, uuid.uuid4())


def test_get_order_detail_rejection_is_audited(make_business, make_supplier, make_supplier_profile):
    """THE REAL GAP FOUND AND FIXED -- get_order_detail's own IDOR
    rejection used to leave zero trace. Confirmed it now publishes a
    real, queryable audit record naming the exact requested order id."""
    from src.domains.security.audit.models.audit_event import AuditEventRecord

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Audit Access Denied Co")
    fake_order_id = uuid.uuid4()

    with pytest.raises(OrderNotFoundError):
        order_history_service.get_order_detail(business.id, profile.id, fake_order_id)

    record = (
        AuditEventRecord.query.filter_by(event_name="business.order_access_denied")
        .order_by(AuditEventRecord.timestamp.desc())
        .first()
    )
    assert record is not None
    assert record.status == "failure"
    assert record.event_metadata["requested_order_id"] == str(fake_order_id)


# --- order reference and buyer snapshot ------------------------------


def test_new_supplier_is_assigned_a_real_supplier_code(make_supplier, make_supplier_profile):
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Supplier Code Co")

    assert profile.supplier_code is not None
    assert len(profile.supplier_code) == 4


def test_submit_checkout_assigns_a_real_order_reference(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Order Reference Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    order = StockOrder.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert order.order_reference is not None
    assert order.order_reference.startswith(f"TRU-{profile.supplier_code}-")
    assert len(order.order_reference) == len("TRU-") + 4 + 1 + 6


def test_submit_checkout_sets_a_real_dedicated_submitted_at(make_business, make_supplier, make_supplier_profile, make_active_connection):
    """THE REAL BUG FIX -- submitted_at is its own column now, never
    reused from updated_at, which a future supplier approve/decline
    would otherwise silently shift."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Submitted At Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    order = StockOrder.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert order.submitted_at is not None


def test_submit_checkout_snapshots_real_buyer_details(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Buyer Snapshot Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    order = StockOrder.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert order.buyer_email == business.email


def test_order_history_shows_the_real_reference_not_a_placeholder(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="History Reference Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    history = order_history_service.list_order_history(business.id, profile.id)

    assert history[0]["orderReference"] is not None
    assert history[0]["orderReference"].startswith("TRU-")


def test_order_detail_includes_real_buyer_information(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Detail Buyer Info Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    detail = order_history_service.get_order_detail(business.id, profile.id, result["id"])

    assert detail["orderReference"] is not None
    assert detail["buyerEmail"] == business.email


# --- notification trigger on checkout ----------------------------------


def test_submit_checkout_notifies_the_supplier(make_business, make_supplier, make_supplier_profile, make_active_connection):
    """THE REAL TRIGGER -- confirms checkout_service.py actually
    publishes a real notification, all the way through the background
    queue to a genuine database row, not just that the call compiles."""
    from src.domains.platform.notifications.repositories.notification_repository import NotificationRepository
    from src.shared.queue.queue import wait_until_idle

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Notify Trigger Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 2)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    wait_until_idle(timeout=5)

    supplier_notifications = NotificationRepository.list_for_user(supplier_user.id, category="STOCK_ORDER")
    assert len(supplier_notifications) == 1
    assert supplier_notifications[0].category == "STOCK_ORDER"
    assert result["orderReference"] in supplier_notifications[0].body
    assert "R20.00" in supplier_notifications[0].body


# --- the real, missing connection constraint (found and fixed) -------


def test_checkout_succeeds_without_a_connection_for_an_ordinary_supplier(
    make_business, make_supplier, make_supplier_profile
):
    """THE V2 STEP 4 BEHAVIOUR CHANGE, at the point it actually matters.

    This exact scenario raised SupplierNotConnectedError before.
    Connection stopped being a platform rule and became a per-supplier
    choice that defaults off, so a business can now buy from a supplier
    it has never connected to -- which is what makes a discovery feed
    worth having at all.

    Order accept/decline remains the supplier's real control, and it is
    a better one: per-transaction, and they can see what is actually
    being ordered."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Open For Business Co")
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert result["status"] == "PENDING_SUPPLIER_APPROVAL", (
        "the supplier still decides per order -- ordering opened up, approval did not disappear"
    )


def test_checkout_rejects_with_no_connection_when_the_supplier_requires_one(
    make_business, make_supplier, make_supplier_profile
):
    """The opt-in path. A supplier who wants to approve businesses
    before stock moves turns requires_connection on and gets exactly the
    behaviour every supplier used to have.

    Browsing and building a cart stay allowed without one, unchanged --
    only the real financial commitment is refused."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user, business_name="No Connection Co", requires_connection=True
    )
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)  # still allowed, unchanged

    with pytest.raises(SupplierNotConnectedError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")


def test_checkout_rejects_a_still_pending_connection_request(
    make_business, make_supplier, make_supplier_profile
):
    """A request that hasn't been approved yet is not the same as an
    active connection -- checkout must still be rejected."""
    from src.domains.network.connections.services import (
        connection_list_service,
        request_service,
    )

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user, business_name="Pending Only Co", requires_connection=True
    )
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    request_service.request_connection(business.id, profile.id)  # sent, never approved

    with pytest.raises(SupplierNotConnectedError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")


def test_checkout_rejects_after_a_real_disconnect_and_re_request(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE EXACT SCENARIO REPRODUCED FROM A REAL, REPORTED LOG:
    connect, approve, checkout succeeds -- then disconnect, send a new
    request (still pending), and checkout must be rejected again, not
    silently still allowed from the old, now-ended connection."""
    from src.domains.network.connections.services import (
        connection_list_service,
        request_service,
    )

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user, business_name="Disconnect Reconnect Co", requires_connection=True
    )
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"

    connection_list_service.end_connection(business.id, profile.id, "NO_LONGER_NEEDED", None)
    cart_service.add_item(business.id, profile.id, product.id, 1)
    request_service.request_connection(business.id, profile.id)  # new, still pending

    with pytest.raises(SupplierNotConnectedError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")


def test_checkout_succeeds_once_the_connection_is_genuinely_active(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """The positive case, confirmed alongside the rejections above --
    this constraint genuinely allows a real, active connection through,
    not just rejects everything."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Active Allowed Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


# --- delivery location fields (Mapbox pin-drop feature) --------------------


def test_deliver_order_persists_structured_delivery_fields(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """The real point of the whole feature: a DELIVER order's pin
    coordinates and structured address actually land on the row, not
    just delivery_address_text."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Pin Drop Co")
    # This test submits a DELIVER order, so the supplier must be one
    # that actually delivers -- offers_delivery defaults False (the
    # cautious default) and checkout now genuinely enforces it.
    profile.offers_delivery = True
    db.session.commit()
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(
        business.id,
        profile.id,
        "CASH",
        "DELIVER",
        "12 Church Street, Westenburg, Polokwane, Limpopo, 0699",
        None,
        "Church Street",
        "Westenburg",
        "Polokwane",
        "Limpopo",
        "0699",
        -23.9045,
        29.4587,
    )

    stock_order = db.session.get(StockOrder, uuid.UUID(result["id"]))
    assert stock_order.delivery_street == "Church Street"
    assert stock_order.delivery_suburb == "Westenburg"
    assert stock_order.delivery_city == "Polokwane"
    assert stock_order.delivery_province == "Limpopo"
    assert stock_order.delivery_postal_code == "0699"
    # Numeric columns come back as Decimal -- compare via float rather
    # than assuming exact type equality with the plain float passed in.
    assert float(stock_order.delivery_latitude) == pytest.approx(-23.9045)
    assert float(stock_order.delivery_longitude) == pytest.approx(29.4587)


def test_collect_order_never_persists_structured_delivery_fields(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL GUARD this test exists to confirm: a COLLECT order
    shows the SUPPLIER's own address, never something the business
    entered -- so even if a buggy or malicious client sends delivery
    coordinates alongside a COLLECT submission, none of it is ever
    written. Only delivery_type itself is meaningful for COLLECT."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Collect Only Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(
        business.id,
        profile.id,
        "CASH",
        "COLLECT",
        None,
        "Suspicious building",
        "Suspicious street",
        "Suspicious suburb",
        "Suspicious city",
        "Suspicious province",
        "0000",
        -1.0,
        1.0,
    )

    stock_order = db.session.get(StockOrder, uuid.UUID(result["id"]))
    assert stock_order.delivery_building is None
    assert stock_order.delivery_street is None
    assert stock_order.delivery_suburb is None
    assert stock_order.delivery_city is None
    assert stock_order.delivery_province is None
    assert stock_order.delivery_postal_code is None
    assert stock_order.delivery_latitude is None
    assert stock_order.delivery_longitude is None


def test_deliver_order_without_any_delivery_fields_still_works(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """Backward compatibility: a DELIVER checkout that only sends the
    old delivery_address_text (e.g. before the frontend adopts the
    map picker) must keep working exactly as before -- every new
    field is optional, defaulting to None, never required."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Old Client Co")
    # Submits a DELIVER order -- see the same note on the test above.
    profile.offers_delivery = True
    db.session.commit()
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(
        business.id, profile.id, "CASH", "DELIVER", "Just some typed text address"
    )

    stock_order = db.session.get(StockOrder, uuid.UUID(result["id"]))
    assert stock_order.delivery_address_text == "Just some typed text address"
    assert stock_order.delivery_latitude is None
    assert stock_order.delivery_longitude is None


# --- cancellation_service: business's own self-service cancel --------------


def test_cancel_order_by_business_releases_reservation_and_notifies_supplier(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL PROOF -- a business cancelling their own still-PENDING
    order releases the held stock, same mechanism decline already
    uses on the supplier's side, and the supplier is told so they
    don't waste time reviewing an order that's already gone."""
    from src.domains.platform.notifications.repositories.notification_repository import NotificationRepository

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Business Cancel Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Tomatoes", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 3)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    inventory = InventoryRepository.get_by_product_id(product.id)
    assert inventory.quantity_reserved == 3

    cancelled = cancellation_service.cancel_order_by_business(
        business.id, profile.id, result["id"], reason="changed_mind", details="Found it cheaper elsewhere."
    )

    assert cancelled["status"] == "CANCELLED"
    db.session.expire_all()
    inventory = InventoryRepository.get_by_product_id(product.id)
    assert inventory.quantity_reserved == 0

    supplier_notifs = NotificationRepository.list_for_user(supplier_user.id, category="STOCK_ORDER")
    cancel_notifs = [n for n in supplier_notifs if "cancelled" in n.body]
    assert len(cancel_notifs) == 1


def test_cancel_order_by_business_sets_the_real_fields(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Cancel Fields Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    cancellation_service.cancel_order_by_business(
        business.id, profile.id, result["id"], reason="ordered_by_mistake"
    )

    stock_order = db.session.get(StockOrder, uuid.UUID(result["id"]))
    assert stock_order.status == StockOrderStatus.CANCELLED
    assert stock_order.cancelled_by == "business"
    assert stock_order.cancel_reason == "ordered_by_mistake"
    assert stock_order.cancelled_at is not None
    # Never touched -- the supplier never decided anything here.
    assert stock_order.decided_at is None


def test_cancel_order_by_business_only_works_while_pending(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL GUARD -- once a supplier has confirmed an order, the
    business can no longer self-cancel through this action at all;
    they have to contact the supplier directly."""
    from src.domains.supplier.stock_order_management.services import order_management_service

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Already Confirmed Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    order_management_service.approve_order(profile.id, result["id"])

    with pytest.raises(OrderNotCancellableError):
        cancellation_service.cancel_order_by_business(business.id, profile.id, result["id"], reason="changed_mind")


def test_cancel_order_by_business_rejects_a_reason_only_a_supplier_would_use(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL SPLIT, mirrored -- "out_of_stock" is a supplier's own
    reason, nonsensical coming from a business."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Wrong Reason Set Business Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    with pytest.raises(ValueError):
        cancellation_service.cancel_order_by_business(business.id, profile.id, result["id"], reason="out_of_stock")


def test_cancel_order_by_business_blocks_a_different_business(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL IDOR PROTECTION -- a business must never be able to
    cancel another business's own order, even a genuinely PENDING one
    with a real, valid order id."""
    business = make_business()
    other_business = make_business("cancel-idor-other@example.com")
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="IDOR Cancel Co")
    make_active_connection(business, profile)
    make_active_connection(other_business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    with pytest.raises(OrderNotFoundError):
        cancellation_service.cancel_order_by_business(
            other_business.id, profile.id, result["id"], reason="changed_mind"
        )


def test_cancel_order_by_business_raises_for_a_genuinely_nonexistent_order(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Order Here Business Co")

    with pytest.raises(OrderNotFoundError):
        cancellation_service.cancel_order_by_business(business.id, profile.id, uuid.uuid4(), reason="changed_mind")


# --- The supplier's own fulfilment terms, enforced at checkout ------------
#
# Both are ALSO applied in the checkout UI, but a client is never the
# gate: a stale screen, a resumed session, or a direct API call all
# reach the service, and the supplier can change either term after the
# cart was built. See checkout_service._validate_supplier_fulfilment_terms.


def test_checkout_rejects_deliver_when_the_supplier_does_not_deliver(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    from src.domains.network.orders.errors import DeliveryNotOfferedError

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Collect Only Co")
    profile.offers_delivery = False
    db.session.commit()
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    with pytest.raises(DeliveryNotOfferedError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")


def test_checkout_allows_deliver_when_the_supplier_has_not_stated_terms(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """offers_delivery is TRI-STATE: NULL means "hasn't said", and must
    never be read as "doesn't deliver". This is the regression that a
    plain boolean caused -- 31 checkout tests failed at once because
    every supplier predating the field silently became non-delivering."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Never Said Co")
    assert profile.offers_delivery is None  # the real default: unstated
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


def test_checkout_allows_collect_when_the_supplier_does_not_deliver(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """The same supplier, the same cart -- COLLECT goes through. The
    gate is on the delivery TYPE, never on ordering itself."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Collect Only Co 2")
    profile.offers_delivery = False
    db.session.commit()
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "COLLECT")
    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


def test_checkout_rejects_an_order_below_the_suppliers_minimum(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    from src.domains.network.orders.errors import BelowMinimumOrderError

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Minimum Co")
    profile.offers_delivery = True
    profile.minimum_order_cents = 50_000  # R500
    db.session.commit()
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread", price_cents=1000)  # R10
    cart_service.add_item(business.id, profile.id, product.id, 1)

    with pytest.raises(BelowMinimumOrderError) as exc:
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    # The shortfall rides along so the frontend can say "add R490 more"
    # rather than making the business do the arithmetic.
    assert exc.value.data["shortfallCents"] == 49_000


def test_checkout_allows_an_order_that_meets_the_minimum_exactly(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """Boundary: the minimum is inclusive -- reaching it exactly is
    enough, it isn't "more than"."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Exact Minimum Co")
    profile.offers_delivery = True
    profile.minimum_order_cents = 2000
    db.session.commit()
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 2)  # exactly R20

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


def test_no_minimum_set_means_any_amount_can_check_out(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """NULL minimum genuinely means "no minimum" -- never zero, and
    never a block."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Minimum Co")
    profile.offers_delivery = True
    profile.minimum_order_cents = None
    db.session.commit()
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread", price_cents=100)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"


def test_cart_carries_the_suppliers_fulfilment_terms(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """The checkout SCREEN reads these off the cart so it can default to
    Collect and explain the minimum before a business fills in a form."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Terms Co")
    profile.offers_delivery = False
    profile.minimum_order_cents = 25_000
    profile.collection_street = "12 Main Road"
    profile.collection_suburb = "Elim"
    db.session.commit()
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart = cart_service.add_item(business.id, profile.id, product.id, 1)

    assert cart["supplierOffersDelivery"] is False
    assert cart["supplierMinimumOrderCents"] == 25_000
    assert cart["supplierCollectionAddress"]["street"] == "12 Main Road"


def test_cart_collection_address_is_none_when_the_supplier_never_set_one(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """A dict of all-None fields would render as an empty address block,
    which reads as broken rather than as "not set yet"."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Address Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart = cart_service.add_item(business.id, profile.id, product.id, 1)

    assert cart["supplierCollectionAddress"] is None
