"""
Formal tests converting this session's own direct verification into
permanent coverage -- the full publish -> background thread ->
real database row pipeline, the read-side API functions, the IDOR
protection on marking notifications read, and the exact message
templates.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from src.domains.network.orders.models.stock_order import StockOrder
from src.domains.network.orders.notification_templates.stock_order_templates import (
    build_new_order_notification,
    build_order_confirmed_notification,
    build_order_declined_notification,
)
from src.domains.platform.notifications.repositories.notification_repository import NotificationRepository
from src.domains.platform.notifications.services import notification_service
from src.domains.platform.notifications.services.notification_service import NotificationNotFoundError
from src.shared.notifications.notification_types import NotificationCategory, NotificationEvent
from src.shared.notifications.notifications import publish_notification
from src.shared.queue.queue import wait_until_idle


# --- the real publish -> background thread -> DB row pipeline --------


def test_publish_notification_writes_a_real_row(make_supplier):
    """THE REAL, END-TO-END PROOF -- publishes through the actual
    background queue (never bypassed for a shortcut), waits for that
    background thread to genuinely finish, then confirms the row.
    This is what actually proves the app-context fix works, not just
    that the code compiles."""
    supplier_user = make_supplier()

    publish_notification(
        NotificationEvent(
            recipient_user_id=supplier_user.id,
            category=NotificationCategory.STOCK_ORDER,
            title="New order",
            body="TruConnect: New order TRU-TEST-ABCDEF \u00b7 Amount R50.00 \u00b7 1 Sep",
        )
    )
    wait_until_idle(timeout=5)

    results = NotificationRepository.list_for_user(supplier_user.id)
    assert len(results) == 1
    assert results[0].category == "STOCK_ORDER"
    assert results[0].is_read is False


def test_a_failing_listener_never_raises_to_the_caller(make_supplier, monkeypatch):
    """NEVER RAISES SYNCHRONOUSLY -- a notification failing to send
    must never break the real action that triggered it. Simulates a
    listener that raises, confirms publish_notification itself still
    returns cleanly."""
    supplier_user = make_supplier()

    def _broken_listener(event):
        raise RuntimeError("simulated failure")

    from src.shared.notifications import notifications as notifications_module

    notifications_module.register_listener(_broken_listener)
    try:
        # Must not raise, even though a registered listener will.
        publish_notification(
            NotificationEvent(
                recipient_user_id=supplier_user.id,
                category=NotificationCategory.INBOX,
                title="Test",
                body="Test",
            )
        )
        wait_until_idle(timeout=5)
    finally:
        notifications_module._listeners.remove(_broken_listener)


# --- read-side functions ----------------------------------------------


def test_list_notifications_filters_by_category(make_supplier):
    supplier_user = make_supplier()
    NotificationRepository.create(supplier_user.id, "STOCK_ORDER", "New order", "body")
    NotificationRepository.create(supplier_user.id, "INBOX", "Welcome", "body")

    all_results = notification_service.list_notifications(supplier_user.id)
    stock_only = notification_service.list_notifications(supplier_user.id, "STOCK_ORDER")

    assert len(all_results) == 2
    assert len(stock_only) == 1
    assert stock_only[0].category == "STOCK_ORDER"


def test_unread_count_reflects_real_state(make_supplier):
    supplier_user = make_supplier()
    NotificationRepository.create(supplier_user.id, "STOCK_ORDER", "New order", "body")
    NotificationRepository.create(supplier_user.id, "STOCK_ORDER", "New order", "body")

    assert notification_service.get_unread_count(supplier_user.id) == 2


def test_mark_as_read_reduces_unread_count(make_supplier):
    supplier_user = make_supplier()
    n = NotificationRepository.create(supplier_user.id, "STOCK_ORDER", "New order", "body")

    notification_service.mark_as_read(supplier_user.id, n.id)

    assert notification_service.get_unread_count(supplier_user.id) == 0


def test_mark_as_read_blocks_a_different_user(make_supplier):
    """THE REAL IDOR PROTECTION -- a user must never be able to mark
    a different user's own notification as read, even with a
    genuinely valid notification id."""
    supplier_a = make_supplier()
    supplier_b = make_supplier("idor-notif-b@example.com")
    n = NotificationRepository.create(supplier_a.id, "STOCK_ORDER", "New order", "body")

    with pytest.raises(NotificationNotFoundError):
        notification_service.mark_as_read(supplier_b.id, n.id)


def test_mark_as_read_raises_for_a_genuinely_nonexistent_notification(make_supplier):
    supplier_user = make_supplier()

    with pytest.raises(NotificationNotFoundError):
        notification_service.mark_as_read(supplier_user.id, uuid.uuid4())


def test_mark_all_as_read_is_a_real_batch_update(make_supplier):
    supplier_user = make_supplier()
    NotificationRepository.create(supplier_user.id, "STOCK_ORDER", "New order", "body")
    NotificationRepository.create(supplier_user.id, "INBOX", "Welcome", "body")

    marked = notification_service.mark_all_as_read(supplier_user.id)

    assert marked == 2
    assert notification_service.get_unread_count(supplier_user.id) == 0


# --- templates -- exact message shape ----------------------------------


class _FakeOrder:
    id = "abc-123"
    order_reference = "TRU-7QXM-4K9P2X"
    total_cents = 24000
    submitted_at = None
    created_at = None


def test_new_order_template_matches_the_exact_agreed_wording():
    order = _FakeOrder()
    order.submitted_at = datetime(2026, 8, 31, tzinfo=timezone.utc)

    event = build_new_order_notification(order, "supplier-id", "Thabo's Spaza Shop")

    assert event.body == "TruConnect: New order TRU-7QXM-4K9P2X from Thabo's Spaza Shop \u00b7 Amount R240.00 \u00b7 31 Aug"
    assert event.category == NotificationCategory.STOCK_ORDER
    assert event.related_entity_type == "stock_order"
    assert event.related_entity_id == "abc-123"


def test_order_confirmed_template_matches_the_exact_agreed_wording():
    order = _FakeOrder()
    order.submitted_at = datetime(2026, 8, 31, tzinfo=timezone.utc)

    event = build_order_confirmed_notification(order, "business-id", "Thabo's Wholesale")

    assert event.body == "TruConnect: Order TRU-7QXM-4K9P2X confirmed by Thabo's Wholesale \u00b7 Amount R240.00 \u00b7 31 Aug"


def test_order_declined_template_matches_the_exact_agreed_wording():
    order = _FakeOrder()
    order.submitted_at = datetime(2026, 8, 31, tzinfo=timezone.utc)

    event = build_order_declined_notification(order, "business-id", "Thabo's Wholesale")

    assert event.body == "TruConnect: Order TRU-7QXM-4K9P2X declined by Thabo's Wholesale \u00b7 Amount R240.00 \u00b7 31 Aug"
