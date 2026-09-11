"""
stock_order_templates.py -- the real wording for every stock-order
notification this domain sends. The ONE place this message text is
decided, matching the same discipline as get_status_label on the
frontend (one function, every call site uses it, no drift between
screens).

LIVES IN A DEDICATED notification_templates/ FOLDER, not a single
flat file -- confirmed directly during planning: as more triggers get
added over time (order cancelled, low stock, a future incident
notice), a growing single file becomes exactly the "hard to manage,
hard to fix" problem the same reasoning already argued against for
frontend feature folders. Each new template becomes a new file here,
not a longer file. connections' own notification_templates/ folder
(domains/network/connections/notification_templates/) mirrors this
same shape -- every domain that sends notifications gets its own
folder, not one shared, centralized template location, for the exact
same "shared/notifications must never know what a stock order or a
connection request even is" reasoning already established.

Deliberately lives HERE, in orders, not inside shared/notifications --
the notifications domain must never know what a "stock order" is; it
only ever receives a completely-built NotificationEvent. This is the
file that does the knowing, on behalf of the domain that actually
understands what an order is.

SHORT ON PURPOSE, matching the exact bank-SMS instinct that shaped
this: reference, who, amount, date -- nothing else. A supplier or
business should understand what happened without reading past the
lock screen.
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.domains.network.orders.models.stock_order import StockOrder
from src.shared.notifications.notification_types import NotificationCategory, NotificationEvent


def _format_rand(total_cents: int) -> str:
    """R240.00 -- the one place a cents integer becomes a currency
    string inside a notification body. Not the frontend's own
    formatCents (that's TypeScript, this is Python), but the same
    real shape."""
    return f"R{total_cents / 100:,.2f}"


def _format_short_date(order: StockOrder) -> str:
    """31 Aug -- deliberately just day and month, matching the
    bank-SMS brevity this whole template style is built around. The
    year rarely matters for "did I just get an order," and omitting
    it keeps every message shorter.

    Built manually (day number + separate month abbreviation), not
    strftime("%-d %b") -- %-d is a Linux/glibc-only extension; this
    backend is also genuinely run on Windows (confirmed directly from
    this same project's own local dev logs), where %-d raises
    ValueError rather than silently doing the wrong thing. This
    approach produces the identical result on every platform."""
    moment = order.submitted_at or order.created_at
    if not moment:
        return ""
    return f"{moment.day} {moment.strftime('%b')}"


def build_new_order_notification(order: StockOrder, supplier_user_id: str, buyer_business_name: str) -> NotificationEvent:
    """To the supplier, the moment a real order is placed."""
    body = (
        f"TruConnect: New order {order.order_reference} from {buyer_business_name} "
        f"\u00b7 Amount {_format_rand(order.total_cents)} \u00b7 {_format_short_date(order)}"
    )
    return NotificationEvent(
        recipient_user_id=supplier_user_id,
        category=NotificationCategory.STOCK_ORDER,
        title="New order",
        body=body,
        related_entity_type="stock_order",
        related_entity_id=str(order.id),
    )


def build_direct_receipts_threshold_notification(
    supplier_user_id: str,
    received_cents: int,
    cap_cents: int,
    fraction: float,
) -> NotificationEvent:
    """To the SUPPLIER, when their direct (off-platform) receipts pass
    a warning threshold for the month.

    NOT AN ERROR, AND WORDED SO. A supplier at 75% has done nothing
    wrong -- they have traded well. The message states where they are
    and what happens next; it does not scold, and it does not imply
    anything is presently blocked, because nothing is.

    NO ORDER ATTACHED, unlike every other template in this file. The
    threshold is a property of the month, not of the order that
    happened to cross it -- linking it to one order would invite a
    supplier to think that particular sale was the problem.
    """
    percent = int(round(fraction * 100))
    body = (
        f"TruConnect: You've received {_format_rand(received_cents)} in direct payments this month "
        f"· {percent}% of your {_format_rand(cap_cents)} monthly limit"
    )
    return NotificationEvent(
        recipient_user_id=supplier_user_id,
        category=NotificationCategory.STOCK_ORDER,
        title="Direct payments this month",
        body=body,
        related_entity_type="supplier_direct_receipts",
        # The MONTH is the thing this is about, so that is what it
        # points at -- and it doubles as the natural key for "have we
        # already told them this", one notification per threshold per
        # month rather than one per order after they cross it.
        related_entity_id=f"{datetime.now(timezone.utc):%Y-%m}:{percent}",
    )


def build_order_confirmed_notification(order: StockOrder, business_user_id: str, supplier_business_name: str) -> NotificationEvent:
    """To the business, the moment a supplier approves -- real and
    wired (domains.supplier.stock_order_management's own
    approve_order calls this directly)."""
    body = (
        f"TruConnect: Order {order.order_reference} confirmed by {supplier_business_name} "
        f"\u00b7 Amount {_format_rand(order.total_cents)} \u00b7 {_format_short_date(order)}"
    )
    return NotificationEvent(
        recipient_user_id=business_user_id,
        category=NotificationCategory.STOCK_ORDER,
        title="Order confirmed",
        body=body,
        related_entity_type="stock_order",
        related_entity_id=str(order.id),
    )


def build_order_declined_notification(order: StockOrder, business_user_id: str, supplier_business_name: str) -> NotificationEvent:
    """To the business, the moment a supplier declines -- real and
    wired, same reasoning as build_order_confirmed_notification
    above."""
    body = (
        f"TruConnect: Order {order.order_reference} declined by {supplier_business_name} "
        f"\u00b7 Amount {_format_rand(order.total_cents)} \u00b7 {_format_short_date(order)}"
    )
    return NotificationEvent(
        recipient_user_id=business_user_id,
        category=NotificationCategory.STOCK_ORDER,
        title="Order declined",
        body=body,
        related_entity_type="stock_order",
        related_entity_id=str(order.id),
    )


def build_order_cancelled_by_business_notification(
    order: StockOrder, supplier_user_id: str, buyer_business_name: str
) -> NotificationEvent:
    """To the SUPPLIER, the moment a business cancels their own still-
    PENDING order -- the one real reason this exists at all: without
    it, a supplier could spend time reviewing an order the business
    already walked away from. Only reachable while PENDING_SUPPLIER_APPROVAL
    (see cancellation_service.cancel_order_by_business's own docstring)."""
    body = (
        f"TruConnect: Order {order.order_reference} from {buyer_business_name} was cancelled "
        f"\u00b7 Amount {_format_rand(order.total_cents)} \u00b7 {_format_short_date(order)}"
    )
    return NotificationEvent(
        recipient_user_id=supplier_user_id,
        category=NotificationCategory.STOCK_ORDER,
        title="Order cancelled",
        body=body,
        related_entity_type="stock_order",
        related_entity_id=str(order.id),
    )


def build_order_cancelled_by_supplier_notification(
    order: StockOrder, business_user_id: str, supplier_business_name: str
) -> NotificationEvent:
    """To the BUSINESS, the moment a supplier cancels an order that was
    already CONFIRMED -- the harder of the two directions, since this
    business may have been genuinely counting on it. Only reachable
    from CONFIRMED (see cancellation_service.cancel_order_by_supplier's
    own docstring) -- a real, considered action, not a casual one."""
    body = (
        f"TruConnect: Order {order.order_reference} cancelled by {supplier_business_name} "
        f"\u00b7 Amount {_format_rand(order.total_cents)} \u00b7 {_format_short_date(order)}"
    )
    return NotificationEvent(
        recipient_user_id=business_user_id,
        category=NotificationCategory.STOCK_ORDER,
        title="Order cancelled",
        body=body,
        related_entity_type="stock_order",
        related_entity_id=str(order.id),
    )


def build_order_reminder_notification(order: StockOrder, supplier_user_id: str, buyer_business_name: str) -> NotificationEvent:
    """To the supplier, when a real order has sat unanswered past a
    real threshold -- see stock_order_reminder_sweep_job.py for the
    actual 24h/3-day timing this fires on. Same short, scannable
    shape as every other stock-order message, with "still waiting"
    replacing the event verb so it reads as a nudge, not a duplicate
    of the original new-order ping."""
    body = (
        f"TruConnect: Order {order.order_reference} from {buyer_business_name} is still waiting on you "
        f"\u00b7 Amount {_format_rand(order.total_cents)} \u00b7 {_format_short_date(order)}"
    )
    return NotificationEvent(
        recipient_user_id=supplier_user_id,
        category=NotificationCategory.STOCK_ORDER,
        title="Order awaiting your response",
        body=body,
        related_entity_type="stock_order",
        related_entity_id=str(order.id),
    )


def build_order_auto_declined_notification(order: StockOrder, business_user_id: str, supplier_business_name: str) -> NotificationEvent:
    """To the business, when stock_order_auto_decline_sweep_job.py
    closes out an order that never got a real decision. Deliberately
    a SEPARATE template from build_order_declined_notification, not a
    reused call with a different reason string -- the two are
    genuinely different events. A manual decline is the supplier
    telling the business no; this is TruConnect telling the business
    the supplier simply never answered. Saying "declined by X" here
    would misrepresent what actually happened as a deliberate business
    decision, when it wasn't one."""
    body = (
        f"TruConnect: Order {order.order_reference} wasn't answered by {supplier_business_name} in time "
        f"and was automatically closed \u00b7 Amount {_format_rand(order.total_cents)}"
    )
    return NotificationEvent(
        recipient_user_id=business_user_id,
        category=NotificationCategory.STOCK_ORDER,
        title="Order automatically closed",
        body=body,
        related_entity_type="stock_order",
        related_entity_id=str(order.id),
    )
