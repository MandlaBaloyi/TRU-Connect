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

from src.domains.network.orders.services import cart_service, checkout_service, order_history_service
from src.domains.network.orders.services.commission import calculate_platform_commission_cents
from src.domains.business.order_limits.tiers.free import LIMITS as FREE_LIMITS
from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
from src.domains.supplier.products.models.product import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.products.services import product_service
from src.extensions import db
from src.domains.network.orders.errors import (
    CartItemNotFoundError,
    CartNotFoundError,
    EmptyCartError,
    OutOfStockError,
    InvalidQuantityError,
    OrderLimitExceededError,
    PaymentMethodNotAvailableError,
    ProductNotFoundError,
    StaleCartItemError,
    SupplierNotFoundError,
)
from src.domains.network.orders.models.stock_order import StockOrder, StockOrderPaymentMethod, StockOrderStatus
from src.domains.network.orders.models.stock_order_payment import StockOrderPayment, StockOrderPaymentStatus
from src.domains.network.orders.providers.composition import get_payment_provider, reset_payment_providers
from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository


def _make_product(profile_id, name="Product", category=ProductCategory.OTHER, price_cents=1000, selling_unit=ProductUnit.EACH, in_stock=True):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    product = ProductRepository.create(
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


def test_submit_checkout_with_no_cart_raises(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Cart Checkout Co")

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


def test_submit_checkout_succeeds_with_cash(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Cash Checkout Co")
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 2)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "COLLECT")

    assert result["status"] == "SUBMITTED"
    assert result["totalCents"] == 2000
    assert result["instructions"] is not None


def test_submit_checkout_succeeds_with_proof_of_payment(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="POP Checkout Co")
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "PROOF_OF_PAYMENT", "DELIVER")

    assert result["status"] == "SUBMITTED"


def test_submit_checkout_leaves_no_active_cart_behind(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Active After Co")
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)

    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert cart_service.get_cart(business.id, profile.id) is None


def test_cannot_resubmit_an_already_submitted_order(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Resubmit Co")
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    with pytest.raises(CartNotFoundError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")


def test_submit_checkout_rejects_an_empty_cart(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Empty Checkout Co")
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    cart_service.remove_item(business.id, profile.id, product.id)

    with pytest.raises(EmptyCartError):
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")


def test_submit_checkout_rejects_a_stale_archived_item_and_names_it(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Stale Item Co")
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


def test_submit_checkout_creates_a_real_payment_record(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Payment Record Co")
    product = _make_product(profile.id, "Item", price_cents=10000)
    cart_service.add_item(business.id, profile.id, product.id, 2)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    payment = StockOrderPayment.query.filter_by(stock_order_id=result["id"]).first()
    assert payment is not None
    assert payment.status == StockOrderPaymentStatus.SUCCEEDED
    assert payment.payment_method == "CASH"
    assert payment.amount_cents == 20000
    assert payment.platform_commission_cents == 0
    assert payment.completed_at is not None


# --- provider isolation ---------------------------------------------------


def test_manual_checkout_works_with_zero_payfast_config(monkeypatch):
    for var in ["PAYFAST_MERCHANT_ID", "PAYFAST_MERCHANT_KEY", "PAYFAST_PASSPHRASE"]:
        monkeypatch.delenv(var, raising=False)
    reset_payment_providers()

    cash_provider = get_payment_provider(StockOrderPaymentMethod.CASH)
    outcome = cash_provider.process_checkout(stock_order=None, payment_method=StockOrderPaymentMethod.CASH)
    assert outcome.order_status == StockOrderStatus.SUBMITTED
    assert outcome.instructions is not None

    pop_provider = get_payment_provider(StockOrderPaymentMethod.PROOF_OF_PAYMENT)
    outcome = pop_provider.process_checkout(stock_order=None, payment_method=StockOrderPaymentMethod.PROOF_OF_PAYMENT)
    assert outcome.order_status == StockOrderStatus.SUBMITTED


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


def test_cash_order_within_the_per_transaction_cap_succeeds(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Within Cash Cap Co")
    product = _make_product(profile.id, "Item", price_cents=FREE_LIMITS.cash_transaction_cap_cents)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert result["status"] == "SUBMITTED"


def test_cash_order_over_the_per_transaction_cap_is_rejected(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Over Cash Cap Co")
    product = _make_product(profile.id, "Item", price_cents=FREE_LIMITS.cash_transaction_cap_cents + 1)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    with pytest.raises(OrderLimitExceededError) as exc_info:
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert exc_info.value.data["reason"] == "PER_TRANSACTION_LIMIT"
    assert exc_info.value.data["limitCents"] == FREE_LIMITS.cash_transaction_cap_cents


def test_proof_of_payment_has_its_own_higher_per_transaction_cap(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL DIFFERENTIATION -- proof-of-payment's own cap is
    genuinely different from cash's, matching the real tier numbers,
    not a single shared limit applied to both."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="POP Higher Cap Co")
    # Over the CASH cap, but within the POP cap.
    assert FREE_LIMITS.proof_of_payment_transaction_cap_cents > FREE_LIMITS.cash_transaction_cap_cents
    product = _make_product(profile.id, "Item", price_cents=FREE_LIMITS.cash_transaction_cap_cents + 1)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "PROOF_OF_PAYMENT", "DELIVER")

    assert result["status"] == "SUBMITTED"


def test_monthly_cumulative_cap_is_enforced_across_multiple_separate_orders(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL LOOPHOLE FIX, proven directly -- confirmed after
    review that a per-transaction cap alone can be defeated by simply
    placing several smaller orders instead of one large one. This
    proves the cumulative check catches that pattern across genuinely
    separate submit_checkout calls, not just within one."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Monthly Cumulative Co")
    # Each order individually under BOTH per-transaction caps, but
    # together they exceed the monthly cap.
    per_order_cents = FREE_LIMITS.cash_transaction_cap_cents
    orders_to_hit_cap = FREE_LIMITS.monthly_manual_payment_cap_cents // per_order_cents

    product = _make_product(profile.id, "Item", price_cents=per_order_cents)
    for _ in range(orders_to_hit_cap):
        cart_service.add_item(business.id, profile.id, product.id, 1)
        result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
        assert result["status"] == "SUBMITTED"

    # One more, individually still within the per-transaction cap, must
    # now be rejected on the CUMULATIVE total.
    cart_service.add_item(business.id, profile.id, product.id, 1)
    with pytest.raises(OrderLimitExceededError) as exc_info:
        checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert exc_info.value.data["reason"] == "MONTHLY_CUMULATIVE_LIMIT"
    assert exc_info.value.data["alreadySpentThisMonthCents"] == orders_to_hit_cap * per_order_cents


def test_monthly_cumulative_cap_is_shared_across_cash_and_proof_of_payment(
    make_business, make_supplier, make_supplier_profile
):
    """THE SECOND HALF OF THE SAME LOOPHOLE FIX -- switching payment
    METHOD between orders must not reset the running total either."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Shared Cap Co")
    product = _make_product(profile.id, "Item", price_cents=FREE_LIMITS.cash_transaction_cap_cents)

    cart_service.add_item(business.id, profile.id, product.id, 1)
    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    remaining = FREE_LIMITS.monthly_manual_payment_cap_cents - FREE_LIMITS.cash_transaction_cap_cents
    if remaining < FREE_LIMITS.cash_transaction_cap_cents:
        # Not enough room left for another full cash-cap order --
        # confirm the SAME running total is visible from the POP side.
        cart_service.add_item(business.id, profile.id, product.id, 1)
        with pytest.raises(OrderLimitExceededError) as exc_info:
            checkout_service.submit_checkout(business.id, profile.id, "PROOF_OF_PAYMENT", "DELIVER")
        assert exc_info.value.data["alreadySpentThisMonthCents"] == FREE_LIMITS.cash_transaction_cap_cents


def test_order_at_exactly_the_per_transaction_cap_is_allowed(make_business, make_supplier, make_supplier_profile):
    """The cap is inclusive -- exactly at it succeeds, only strictly
    over it is rejected."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Exactly At Cap Co")
    product = _make_product(profile.id, "Item", price_cents=FREE_LIMITS.cash_transaction_cap_cents)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    assert result["status"] == "SUBMITTED"


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


def test_order_history_shows_a_real_submitted_order(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Real History Co")
    product = _make_product(profile.id, "Bread", price_cents=1000)
    cart_service.add_item(business.id, profile.id, product.id, 2)
    checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    history = order_history_service.list_order_history(business.id, profile.id)

    assert len(history) == 1
    assert history[0]["status"] == "SUBMITTED"
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


def test_order_history_is_scoped_to_one_supplier(make_business, make_supplier, make_supplier_profile):
    """A business's order from Supplier A must never appear in
    Supplier B's own history list."""
    business = make_business()
    supplier_a = make_supplier("history-scope-a@example.com")
    profile_a = make_supplier_profile(supplier_a, business_name="History Scope A")
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
