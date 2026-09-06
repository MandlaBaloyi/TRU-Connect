"""
order_management_service -- the real supplier-side actions this whole
domain exists for: approve and decline a PENDING_SUPPLIER_APPROVAL
order. Deliberately separate from domains.network.orders' own
checkout_service.py/cart_service.py -- those are the business-facing
half of an order's lifecycle; this is the supplier-facing half. Both
read and mutate the SAME StockOrder rows, via the SAME
StockOrderRepository, matching the established "shared/orders holds
the neutral data, each role's own domain holds its own rules" shape
already proven for the business side.
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from src.domains.network.orders.models.stock_order import (
    StockOrderCancelledBy,
    StockOrderCancelReason,
    StockOrderDeclineReason,
    StockOrderPaymentMethod,
    StockOrderStatus,
)
from src.domains.network.orders.notification_templates.stock_order_templates import (
    build_order_auto_declined_notification,
    build_order_cancelled_by_supplier_notification,
    build_order_confirmed_notification,
    build_order_declined_notification,
)
from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository
from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.products.services import product_media_service
from src.domains.supplier.stock_order_management.errors import (
    DigitalPaymentCancellationNotSupportedError,
    OrderNotConfirmedError,
    OrderNotFoundError,
    OrderNotPendingError,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.extensions import db
from src.shared.audit.audit import publish
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditStatus
from src.shared.audit.event_types.supplier import SupplierAuditEvent
from src.shared.notifications.notifications import publish_notification


def _serialize_order_summary(order) -> dict:
    return {
        "id": str(order.id),
        "orderReference": order.order_reference,
        "status": order.status.value,
        "totalCents": order.total_cents,
        "itemCount": len([i for i in order.items if not i.is_deleted]),
        "paymentMethod": order.payment_method.value if order.payment_method else None,
        "deliveryType": order.delivery_type.value if order.delivery_type else None,
        "submittedAt": order.submitted_at.isoformat() if order.submitted_at else None,
        "decidedAt": order.decided_at.isoformat() if order.decided_at else None,
        "buyerName": order.buyer_name,
        "buyerPhone": order.buyer_phone,
        "buyerBusinessName": order.buyer_business_name,
        "buyerEmail": order.buyer_email,
        # Only meaningful when status is DECLINED -- included on the
        # summary shape (not just get_order_detail's own extra
        # fields) since the Declined tab's own cards show the real
        # reason without a tap-through.
        "declineReason": order.decline_reason,
        # Only meaningful when status is CANCELLED.
        "cancelledBy": order.cancelled_by,
        "cancelReason": order.cancel_reason,
        "cancelledAt": order.cancelled_at.isoformat() if order.cancelled_at else None,
    }


def list_pending_orders(supplier_profile_id: str | UUID) -> List[dict]:
    """A supplier's own real "incoming orders" queue -- every order
    genuinely waiting on their decision right now."""
    orders = StockOrderRepository.list_pending_for_supplier(supplier_profile_id)
    return [_serialize_order_summary(order) for order in orders]


def list_orders_by_status(
    supplier_profile_id: str | UUID,
    status: str,
    submitted_from: Optional[datetime] = None,
    submitted_to: Optional[datetime] = None,
) -> List[dict]:
    """The Approved/Declined tabs' own real listing -- a supplier's
    full history for one specific status, optionally narrowed to a
    real date range (today / this week / this month / this year --
    see the frontend's own date-filter for how those map to real
    from/to timestamps)."""
    if status not in [s.value for s in StockOrderStatus]:
        raise ValueError(f"'{status}' isn't a real order status.")
    orders = StockOrderRepository.list_by_status_for_supplier(
        supplier_profile_id, StockOrderStatus(status), submitted_from, submitted_to
    )
    return [_serialize_order_summary(order) for order in orders]


def get_order_detail(supplier_profile_id: str | UUID, order_id: str | UUID) -> dict:
    """The supplier's own full detail view -- IDOR-safe by
    construction, scoped from the supplier's own side (the mirror
    image of order_history_service.get_order_detail's own
    business-side version)."""
    order = StockOrderRepository.get_by_id_for_supplier(order_id, supplier_profile_id)
    if not order:
        raise OrderNotFoundError("Order not found.")

    items = []
    for item in order.items:
        if item.is_deleted:
            continue
        product = ProductRepository.get_by_id_and_supplier(item.product_id, supplier_profile_id)
        items.append(
            {
                "productId": str(item.product_id),
                "productName": product.name if product else "(no longer available)",
                "images": product_media_service.list_approved_media(item.product_id) if product else [],
                "quantity": item.quantity,
                "priceCentsAtAddTime": item.price_cents_at_add_time,
                "lineTotalCents": item.quantity * item.price_cents_at_add_time,
            }
        )

    return {
        **_serialize_order_summary(order),
        "deliveryAddressText": order.delivery_address_text,
        "declineDetails": order.decline_details,
        "cancelDetails": order.cancel_details,
        "items": items,
    }


def approve_order(supplier_profile_id: str | UUID, order_id: str | UUID) -> dict:
    """PENDING_SUPPLIER_APPROVAL -> CONFIRMED. The business is
    notified the moment this happens -- see
    build_order_confirmed_notification's own docstring, now genuinely
    reachable rather than the "not reachable yet" placeholder it was
    built as."""
    order = StockOrderRepository.get_by_id_for_supplier(order_id, supplier_profile_id)
    if not order:
        raise OrderNotFoundError("Order not found.")
    if order.status != StockOrderStatus.PENDING_SUPPLIER_APPROVAL:
        raise OrderNotPendingError("This order has already been decided on.")

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    order.status = StockOrderStatus.CONFIRMED
    order.decided_at = datetime.now(timezone.utc)
    db.session.commit()

    publish_notification(
        build_order_confirmed_notification(
            order,
            business_user_id=str(order.business_id),
            supplier_business_name=supplier.business_name if supplier else "Your supplier",
        )
    )
    publish(
        AuditEvent(
            event_name=SupplierAuditEvent.ORDER_APPROVED,
            domain=AuditDomain.SUPPLIER,
            status=AuditStatus.SUCCESS,
            metadata={"supplier_profile_id": str(supplier_profile_id), "order_id": str(order.id)},
        )
    )

    return _serialize_order_summary(order)


def _apply_decline(order, reason: str, details: Optional[str]) -> None:
    """The core, real state change shared by BOTH decline paths --
    manual (decline_order, below) and automatic
    (auto_decline_order, below). Deliberately extracted so the two
    can never drift apart: a future fix to the reservation-release
    logic lands in exactly one place, not two copies that could
    silently diverge. Does NOT send any notification or audit event
    itself -- those genuinely differ between the two callers (see
    build_order_auto_declined_notification's own docstring for why),
    so each caller sends its own."""
    order.status = StockOrderStatus.DECLINED
    order.decline_reason = reason
    order.decline_details = details
    order.decided_at = datetime.now(timezone.utc)

    for item in order.items:
        if item.is_deleted:
            continue
        inventory = InventoryRepository.get_by_product_id(item.product_id)
        if inventory:
            InventoryRepository.reserve_quantity(inventory, -item.quantity)

    db.session.commit()


def decline_order(
    supplier_profile_id: str | UUID, order_id: str | UUID, reason: str, details: Optional[str] = None
) -> dict:
    """PENDING_SUPPLIER_APPROVAL -> DECLINED, a supplier's own real,
    manual decision. THE REAL RESERVATION RELEASE --
    InventoryRepository.reserve_quantity's own negative-delta support
    existed since it was first built, never called until now; this is
    the moment it's genuinely needed (see _apply_decline above). The
    business is notified the moment this happens too."""
    if reason not in [r.value for r in StockOrderDeclineReason]:
        raise ValueError(f"'{reason}' isn't a real decline reason.")

    order = StockOrderRepository.get_by_id_for_supplier(order_id, supplier_profile_id)
    if not order:
        raise OrderNotFoundError("Order not found.")
    if order.status != StockOrderStatus.PENDING_SUPPLIER_APPROVAL:
        raise OrderNotPendingError("This order has already been decided on.")

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    _apply_decline(order, reason, details)

    publish_notification(
        build_order_declined_notification(
            order,
            business_user_id=str(order.business_id),
            supplier_business_name=supplier.business_name if supplier else "Your supplier",
        )
    )
    publish(
        AuditEvent(
            event_name=SupplierAuditEvent.ORDER_DECLINED,
            domain=AuditDomain.SUPPLIER,
            status=AuditStatus.SUCCESS,
            metadata={
                "supplier_profile_id": str(supplier_profile_id),
                "order_id": str(order.id),
                "reason": reason,
            },
        )
    )

    return _serialize_order_summary(order)


# The real, enforced subset a SUPPLIER is allowed to choose from --
# business-side reasons (CHANGED_MIND etc.) describe something only a
# business could actually know; offering them to a supplier would be
# nonsensical, not just superfluous. See
# domains.network.orders.services.cancellation_service's own
# BUSINESS_CANCEL_REASONS for the mirror image of this constant.
SUPPLIER_CANCEL_REASONS = {
    StockOrderCancelReason.OUT_OF_STOCK.value,
    StockOrderCancelReason.CANNOT_FULFIL_DELIVERY_AREA.value,
    StockOrderCancelReason.PRICING_ERROR.value,
    StockOrderCancelReason.OTHER.value,
}


def cancel_order(
    supplier_profile_id: str | UUID, order_id: str | UUID, reason: str, details: Optional[str] = None
) -> dict:
    """CONFIRMED -> CANCELLED, the supplier's own real, considered
    decision to walk back an order they already approved. THE ONLY
    PATH a CONFIRMED order can be cancelled through at all -- once
    confirmed, the business itself can no longer self-cancel via the
    app (domains.network.orders.services.cancellation_service.py's
    own cancel_order_by_business explicitly refuses this); if a
    business calls asking to cancel, this is the supplier's own tool
    for acting on that. Genuinely NOT the same door as decline_order
    above -- that one only ever applies to a still-PENDING order.

    Releases the same held stock reservation decline does -- a
    CONFIRMED order still holds its reservation (nothing releases it
    on approval; see InventoryRepository.reserve_quantity's own
    docstring), so cancelling one afterward needs the exact same
    release _apply_decline already performs, or that stock would stay
    falsely reserved forever with no real order behind it."""
    if reason not in SUPPLIER_CANCEL_REASONS:
        raise ValueError(f"'{reason}' isn't a real cancellation reason for a supplier.")

    order = StockOrderRepository.get_by_id_for_supplier(order_id, supplier_profile_id)
    if not order:
        raise OrderNotFoundError("Order not found.")

    if order.payment_method == StockOrderPaymentMethod.PAYFAST:
        raise DigitalPaymentCancellationNotSupportedError(
            "Online payments need their own cancellation and refund flow -- contact support."
        )

    if order.status != StockOrderStatus.CONFIRMED:
        raise OrderNotConfirmedError("Only a confirmed order can be cancelled this way.")

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)

    order.status = StockOrderStatus.CANCELLED
    order.cancelled_by = StockOrderCancelledBy.SUPPLIER.value
    order.cancel_reason = reason
    order.cancel_details = details
    order.cancelled_at = datetime.now(timezone.utc)

    for item in order.items:
        if item.is_deleted:
            continue
        inventory = InventoryRepository.get_by_product_id(item.product_id)
        if inventory:
            InventoryRepository.reserve_quantity(inventory, -item.quantity)

    db.session.commit()

    publish_notification(
        build_order_cancelled_by_supplier_notification(
            order,
            business_user_id=str(order.business_id),
            supplier_business_name=supplier.business_name if supplier else "Your supplier",
        )
    )
    publish(
        AuditEvent(
            event_name=SupplierAuditEvent.ORDER_CANCELLED,
            domain=AuditDomain.SUPPLIER,
            status=AuditStatus.SUCCESS,
            metadata={
                "supplier_profile_id": str(supplier_profile_id),
                "order_id": str(order.id),
                "reason": reason,
            },
        )
    )

    return _serialize_order_summary(order)


def auto_decline_order(order) -> None:
    """PENDING_SUPPLIER_APPROVAL -> DECLINED, closed out
    automatically by stock_order_auto_decline_sweep_job.py because it
    sat unanswered past the real, final timeout -- never called from
    an API route, so it takes the already-fetched order object
    directly rather than an id (the job already has it from
    StockOrderRepository.list_awaiting_auto_decline, and this is a
    system-to-system call with no IDOR concern to check). Uses the
    SAME core state change as a manual decline (_apply_decline
    above), but sends the honest, separate auto-decline notification
    and its own audit event -- see
    build_order_auto_declined_notification's own docstring for why
    reusing the manual-decline message would misrepresent what
    actually happened."""
    supplier = SupplierProfileRepository.get_by_id(order.supplier_profile_id)
    _apply_decline(order, StockOrderDeclineReason.NO_RESPONSE.value, None)

    publish_notification(
        build_order_auto_declined_notification(
            order,
            business_user_id=str(order.business_id),
            supplier_business_name=supplier.business_name if supplier else "Your supplier",
        )
    )
    publish(
        AuditEvent(
            event_name=SupplierAuditEvent.ORDER_AUTO_DECLINED,
            domain=AuditDomain.SUPPLIER,
            status=AuditStatus.SUCCESS,
            metadata={"supplier_profile_id": str(order.supplier_profile_id), "order_id": str(order.id)},
        )
    )
