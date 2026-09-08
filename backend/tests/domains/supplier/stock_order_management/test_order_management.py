"""
Formal tests converting this session's own direct verification into
permanent coverage -- the real approve/decline flows, the inventory
reservation release on decline, the business notifications both
actions trigger, and the IDOR protection across every action a
supplier can take.
"""
from __future__ import annotations

import uuid

import pytest

from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.domains.network.orders.models.stock_order import StockOrder
from src.domains.network.orders.services import cart_service, checkout_service
from src.domains.supplier.stock_order_management.errors import (
    OrderNotConfirmedError,
    OrderNotFoundError,
    OrderNotPendingError,
)
from src.domains.supplier.stock_order_management.services import order_management_service
from src.domains.platform.notifications.repositories.notification_repository import NotificationRepository
from src.extensions import db
from src.shared.queue.queue import wait_until_idle


def _make_product(profile_id, name="Product", price_cents=1000, in_stock=True):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    product = SupplierOfferRepository.create(
        profile_id, name, ProductCategory.OTHER, price_cents, ProductUnit.EACH,
        sku=generate_sku(profile_id), product_code=generate_product_code(),
    )
    if in_stock:
        inventory = InventoryRepository.get_or_create_for_product(product.id, profile_id)
        InventoryRepository.adjust_quantity(inventory, 100)
    return product


# --- approve --------------------------------------------------------------


def test_approve_order_confirms_it_and_notifies_the_business(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Approve Flow Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 2)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    wait_until_idle(timeout=5)

    approved = order_management_service.approve_order(profile.id, result["id"])
    wait_until_idle(timeout=5)

    assert approved["status"] == "CONFIRMED"
    notifs = NotificationRepository.list_for_user(business.id, category="STOCK_ORDER")
    confirmed = [n for n in notifs if "confirmed" in n.body]
    assert len(confirmed) == 1
    assert result["orderReference"] in confirmed[0].body


def test_approve_order_sets_decided_at(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Decided At Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    pending_detail = order_management_service.get_order_detail(profile.id, result["id"])
    assert pending_detail["decidedAt"] is None

    approved = order_management_service.approve_order(profile.id, result["id"])

    assert approved["decidedAt"] is not None


def test_decline_order_sets_decided_at(make_business, make_supplier, make_supplier_profile, make_active_connection):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Decided At Decline Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    declined = order_management_service.decline_order(profile.id, result["id"], "out_of_stock")

    assert declined["decidedAt"] is not None


def test_cannot_approve_an_order_that_is_not_pending(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Already Decided Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    order_management_service.approve_order(profile.id, result["id"])

    with pytest.raises(OrderNotPendingError):
        order_management_service.approve_order(profile.id, result["id"])


# --- decline, including the real inventory release -------------------


def test_decline_order_releases_the_reservation_and_notifies_the_business(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL PROOF this whole reservation system was waiting for --
    InventoryRepository.reserve_quantity's own negative-delta support
    existed unused since it was first built; this is what finally
    calls it."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Decline Release Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Tomatoes")
    cart_service.add_item(business.id, profile.id, product.id, 4)
    result = checkout_service.submit_checkout(business.id, profile.id, "PROOF_OF_PAYMENT", "COLLECT")
    wait_until_idle(timeout=5)

    inventory = InventoryRepository.get_by_product_id(product.id)
    assert inventory.quantity_reserved == 4

    declined = order_management_service.decline_order(
        profile.id, result["id"], reason="out_of_stock", details="Ran out this morning."
    )
    wait_until_idle(timeout=5)

    assert declined["status"] == "DECLINED"
    from src.extensions import db as _db
    _db.session.expire_all()
    inventory = InventoryRepository.get_by_product_id(product.id)
    assert inventory.quantity_reserved == 0

    notifs = NotificationRepository.list_for_user(business.id, category="STOCK_ORDER")
    declined_notifs = [n for n in notifs if "declined" in n.body]
    assert len(declined_notifs) == 1


def test_decline_order_requires_a_real_reason(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Real Reason Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    with pytest.raises(ValueError):
        order_management_service.decline_order(profile.id, result["id"], reason="not_a_real_reason")


# --- supplier cancel_order: CONFIRMED -> CANCELLED, the OTHER cancel door --


def test_cancel_order_only_works_on_a_confirmed_order(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL GUARD -- decline_order is the door for a still-PENDING
    order; this is specifically for one already CONFIRMED. A supplier
    must not be able to cancel an order that's still pending through
    this action (that's what decline is for), nor one already
    declined/cancelled."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Not Confirmed Yet Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    with pytest.raises(OrderNotConfirmedError):
        order_management_service.cancel_order(profile.id, result["id"], reason="out_of_stock")


def test_cancel_order_releases_the_reservation_and_notifies_the_business(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL PROOF a CONFIRMED order's reservation genuinely gets
    released -- confirming an order never releases the reservation
    (it's still held stock, waiting to actually be fulfilled), so
    cancelling one afterward must release it explicitly, same
    mechanism as decline."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Cancel Release Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Tomatoes")
    cart_service.add_item(business.id, profile.id, product.id, 5)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    order_management_service.approve_order(profile.id, result["id"])
    wait_until_idle(timeout=5)

    inventory = InventoryRepository.get_by_product_id(product.id)
    assert inventory.quantity_reserved == 5

    cancelled = order_management_service.cancel_order(
        profile.id, result["id"], reason="out_of_stock", details="Discovered we're short after approving."
    )
    wait_until_idle(timeout=5)

    assert cancelled["status"] == "CANCELLED"
    assert cancelled["cancelledBy"] == "supplier"
    assert cancelled["cancelReason"] == "out_of_stock"
    from src.extensions import db as _db

    _db.session.expire_all()
    inventory = InventoryRepository.get_by_product_id(product.id)
    assert inventory.quantity_reserved == 0

    notifs = NotificationRepository.list_for_user(business.id, category="STOCK_ORDER")
    cancelled_notifs = [n for n in notifs if "cancelled" in n.body]
    assert len(cancelled_notifs) == 1


def test_cancel_order_preserves_the_original_confirmation_time(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """decidedAt (when it was first confirmed) must NOT be silently
    overwritten by a later cancellation -- that would lose the real
    fact that this order WAS confirmed once, and when. cancelledAt is
    its own, separate timestamp for exactly this reason."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Preserve Decided At Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    approved = order_management_service.approve_order(profile.id, result["id"])
    original_decided_at = approved["decidedAt"]

    cancelled = order_management_service.cancel_order(profile.id, result["id"], reason="out_of_stock")

    assert cancelled["decidedAt"] == original_decided_at
    detail = order_management_service.get_order_detail(profile.id, result["id"])
    assert detail["cancelledAt"] is not None


def test_cancel_order_rejects_a_reason_only_a_business_would_use(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """THE REAL SPLIT -- "changed_mind" is a business's own reason,
    nonsensical coming from a supplier. Confirms the two reason sets
    are genuinely enforced, not just documented."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Wrong Reason Set Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    order_management_service.approve_order(profile.id, result["id"])

    with pytest.raises(ValueError):
        order_management_service.cancel_order(profile.id, result["id"], reason="changed_mind")


def test_cancel_order_raises_for_a_genuinely_nonexistent_order(make_supplier, make_supplier_profile):
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Order Here Co")

    with pytest.raises(OrderNotFoundError):
        order_management_service.cancel_order(profile.id, uuid.uuid4(), reason="out_of_stock")


def test_get_order_detail_shows_the_real_decline_reason(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Detail Reason Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    order_management_service.decline_order(profile.id, result["id"], reason="pricing_error", details="Typo in price.")

    detail = order_management_service.get_order_detail(profile.id, result["id"])

    assert detail["declineReason"] == "pricing_error"
    assert detail["declineDetails"] == "Typo in price."


def test_cannot_decline_an_order_that_is_not_pending(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Already Approved Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    order_management_service.approve_order(profile.id, result["id"])

    with pytest.raises(OrderNotPendingError):
        order_management_service.decline_order(profile.id, result["id"], reason="out_of_stock")


# --- list_pending_orders ----------------------------------------------


def test_list_pending_orders_shows_a_real_incoming_order(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Pending List Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    pending = order_management_service.list_pending_orders(profile.id)

    assert len(pending) == 1
    assert pending[0]["orderReference"] == result["orderReference"]


def test_list_pending_orders_excludes_already_decided_orders(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Decided Excluded Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    order_management_service.approve_order(profile.id, result["id"])

    pending = order_management_service.list_pending_orders(profile.id)

    assert pending == []


# --- IDOR protection, across every real action -------------------------


def test_idor_protection_across_every_action(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """A supplier must never be able to view, approve, decline, or
    have visible in their own pending list an order genuinely
    belonging to a different supplier -- confirmed across all four
    real entry points, not just one."""
    business = make_business()
    supplier_a = make_supplier("idor-action-a@example.com")
    profile_a = make_supplier_profile(supplier_a, business_name="IDOR Action A")
    make_active_connection(business, profile_a)
    supplier_b = make_supplier("idor-action-b@example.com")
    profile_b = make_supplier_profile(supplier_b, business_name="IDOR Action B")

    product = _make_product(profile_a.id, "Bread")
    cart_service.add_item(business.id, profile_a.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile_a.id, "CASH", "DELIVER")

    with pytest.raises(OrderNotFoundError):
        order_management_service.approve_order(profile_b.id, result["id"])

    with pytest.raises(OrderNotFoundError):
        order_management_service.get_order_detail(profile_b.id, result["id"])

    with pytest.raises(OrderNotFoundError):
        order_management_service.decline_order(profile_b.id, result["id"], reason="other")

    assert order_management_service.list_pending_orders(profile_b.id) == []


def test_actions_raise_for_a_genuinely_nonexistent_order(make_supplier, make_supplier_profile):
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Nonexistent Order Co")

    with pytest.raises(OrderNotFoundError):
        order_management_service.approve_order(profile.id, uuid.uuid4())

    with pytest.raises(OrderNotFoundError):
        order_management_service.get_order_detail(profile.id, uuid.uuid4())


# --- reminders and auto-decline, converting this session's own direct
#     verification into permanent coverage ------------------------------


def test_reminder_sweep_sends_first_reminder_past_24h(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    from datetime import datetime, timedelta, timezone
    from src.domains.supplier.stock_order_management.jobs import reminder_sweep_job

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Reminder 24h Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    order = StockOrder.query.get(result["id"])
    order.submitted_at = datetime.now(timezone.utc) - timedelta(hours=25)
    db.session.commit()

    job_result = reminder_sweep_job.run()

    assert job_result.count == 1
    db.session.expire_all()
    order = StockOrder.query.get(result["id"])
    assert order.first_reminder_sent_at is not None
    notifs = NotificationRepository.list_for_user(supplier_user.id, category="STOCK_ORDER")
    assert len([n for n in notifs if "still waiting" in n.body]) == 1


def test_reminder_sweep_never_sends_the_first_reminder_twice(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    """Running the sweep twice in a row must not double-send --
    first_reminder_sent_at is what makes the query idempotent."""
    from datetime import datetime, timedelta, timezone
    from src.domains.supplier.stock_order_management.jobs import reminder_sweep_job

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Duplicate Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    order = StockOrder.query.get(result["id"])
    order.submitted_at = datetime.now(timezone.utc) - timedelta(hours=25)
    db.session.commit()

    reminder_sweep_job.run()
    second_run = reminder_sweep_job.run()

    assert second_run.count == 0
    notifs = NotificationRepository.list_for_user(supplier_user.id, category="STOCK_ORDER")
    assert len([n for n in notifs if "still waiting" in n.body]) == 1


def test_auto_decline_sweep_closes_out_and_releases_stock(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    from datetime import datetime, timedelta, timezone
    from src.domains.supplier.stock_order_management.jobs import auto_decline_sweep_job

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Auto Decline Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 3)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    order = StockOrder.query.get(result["id"])
    order.submitted_at = datetime.now(timezone.utc) - timedelta(days=8)
    db.session.commit()

    job_result = auto_decline_sweep_job.run()

    assert job_result.count == 1
    db.session.expire_all()
    order = StockOrder.query.get(result["id"])
    assert order.status.value == "DECLINED"
    assert order.decline_reason == "no_response"

    inventory = InventoryRepository.get_by_product_id(product.id)
    assert inventory.quantity_reserved == 0

    notifs = NotificationRepository.list_for_user(business.id, category="STOCK_ORDER")
    assert len([n for n in notifs if "automatically closed" in n.body]) == 1

    assert order_management_service.list_pending_orders(profile.id) == []
    declined = order_management_service.list_orders_by_status(profile.id, "DECLINED")
    assert len(declined) == 1


def test_auto_decline_sweep_ignores_orders_not_yet_due(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    from datetime import datetime, timedelta, timezone
    from src.domains.supplier.stock_order_management.jobs import auto_decline_sweep_job

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Not Due Yet Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")
    cart_service.add_item(business.id, profile.id, product.id, 1)
    result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")

    order = StockOrder.query.get(result["id"])
    order.submitted_at = datetime.now(timezone.utc) - timedelta(days=2)
    db.session.commit()

    job_result = auto_decline_sweep_job.run()

    assert job_result.count == 0
    db.session.expire_all()
    order = StockOrder.query.get(result["id"])
    assert order.status.value == "PENDING_SUPPLIER_APPROVAL"


def test_list_orders_by_status_supports_a_real_date_range(
    make_business, make_supplier, make_supplier_profile, make_active_connection
):
    from datetime import datetime, timedelta, timezone

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Date Range Co")
    make_active_connection(business, profile)
    product = _make_product(profile.id, "Bread")

    cart_service.add_item(business.id, profile.id, product.id, 1)
    old_result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    order_management_service.approve_order(profile.id, old_result["id"])
    old_order = StockOrder.query.get(old_result["id"])
    old_order.submitted_at = datetime.now(timezone.utc) - timedelta(days=30)
    db.session.commit()

    cart_service.add_item(business.id, profile.id, product.id, 1)
    recent_result = checkout_service.submit_checkout(business.id, profile.id, "CASH", "DELIVER")
    order_management_service.approve_order(profile.id, recent_result["id"])

    recent_only = order_management_service.list_orders_by_status(
        profile.id, "CONFIRMED", submitted_from=datetime.now(timezone.utc) - timedelta(days=1)
    )

    assert len(recent_only) == 1
    assert recent_only[0]["orderReference"] == recent_result["orderReference"]
