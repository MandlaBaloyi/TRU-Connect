"""
cancellation_service.py -- the business's own self-service cancel,
genuinely separate from checkout_service.py (which only ever submits
orders) and order_history_service.py (which only ever views them).

THE FULL ARCHITECTURE, both directions, decided directly with the
person building this app:

  PENDING_SUPPLIER_APPROVAL -- business can cancel any time (THIS
    file, cancel_order_by_business). Matches the real auto-decline
    sweep's own 7-day window (stock_order_management/jobs/
    auto_decline_sweep_job.py) -- a business may genuinely sit on a
    pending order for a while, changing their mind during that whole
    window is a real scenario, not an edge case.

  CONFIRMED -- the business can NOT self-cancel through the app.
    Contacting the supplier directly (real phone/WhatsApp/email,
    already gated by active connection) is the only path from here on
    the business's side. If the supplier agrees, THEY cancel it --
    see stock_order_management/services/order_management_service.py's
    own cancel_order.

  DECLINED / CANCELLED -- already terminal, no action either side.

ONE SHARED cancelled_by / cancel_reason / cancel_details SHAPE across
both directions (see StockOrder model's own StockOrderCancelledBy /
StockOrderCancelReason docstrings) -- cancelled_by tells the two
paths apart; the UI on each side only ever offers the reason subset
relevant to that actor (BUSINESS_CANCEL_REASONS below).

CASH/PROOF_OF_PAYMENT ONLY -- explicitly guarded against PAYFAST,
genuinely unreachable today (see StockOrderPaymentMethod's own
comment) but a real, deliberate guard rather than silent trust: a
digital payment needs its own refund-integrated cancellation flow
through the real payment gateway, never this manual, reason-and-
notify one.
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone
from uuid import UUID

from src.domains.network.orders.errors import (
    DigitalPaymentCancellationNotSupportedError,
    OrderNotCancellableError,
    OrderNotFoundError,
)
from src.domains.network.orders.models.stock_order import (
    StockOrderCancelledBy,
    StockOrderCancelReason,
    StockOrderPaymentMethod,
    StockOrderStatus,
)
from src.domains.network.orders.notification_templates.stock_order_templates import (
    build_order_cancelled_by_business_notification,
)
from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository
from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.extensions import db
from src.shared.audit.audit import publish
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditStatus
from src.shared.audit.event_types.business import BusinessAuditEvent
from src.shared.notifications.notifications import publish_notification
from src.domains.network.orders.models.stock_order_event import (
    StockOrderEventActor,
    StockOrderEventType,
)
from src.domains.network.orders.services import order_event_service

# The real, enforced subset a BUSINESS is allowed to choose from --
# supplier-side reasons (OUT_OF_STOCK etc.) describe something only a
# supplier could actually know, offering them to a business would be
# nonsensical, not just superfluous.
BUSINESS_CANCEL_REASONS = {
    StockOrderCancelReason.CHANGED_MIND.value,
    StockOrderCancelReason.FOUND_ALTERNATIVE.value,
    StockOrderCancelReason.ORDERED_BY_MISTAKE.value,
    StockOrderCancelReason.OTHER.value,
}


def cancel_order_by_business(
    business_id: str | UUID, supplier_profile_id: str | UUID, order_id: str | UUID, reason: str, details: Optional[str] = None
) -> dict:
    if reason not in BUSINESS_CANCEL_REASONS:
        raise ValueError(f"'{reason}' isn't a real cancellation reason for a business.")

    order = StockOrderRepository.get_by_id_for_business_and_supplier(order_id, business_id, supplier_profile_id)
    if not order:
        raise OrderNotFoundError("Order not found.")

    if order.payment_method == StockOrderPaymentMethod.PAYFAST:
        raise DigitalPaymentCancellationNotSupportedError(
            "Online payments need their own cancellation and refund flow -- contact support."
        )

    if order.status != StockOrderStatus.PENDING_SUPPLIER_APPROVAL:
        raise OrderNotCancellableError(
            "This order has already been processed -- contact your supplier directly to cancel it."
        )

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)

    previous_status = order.status
    order.status = StockOrderStatus.CANCELLED
    order.cancelled_by = StockOrderCancelledBy.BUSINESS.value
    order.cancel_reason = reason
    order.cancel_details = details
    order.cancelled_at = datetime.now(timezone.utc)

    # CANCELLED_BY_BUSINESS, not CANCELLED. Both produce the same
    # status, and which side walked away is the thing anybody actually
    # asks -- the status column cannot express it.
    order_event_service.record(
        order,
        StockOrderEventType.CANCELLED_BY_BUSINESS,
        from_status=previous_status,
        actor=StockOrderEventActor.BUSINESS,
        actor_user_id=order.business_id,
        reason=details or reason,
    )

    # THE REAL RESERVATION RELEASE -- identical mechanism to
    # decline_order's own _apply_decline (stock_order_management's own
    # service), called from here since a business-cancelled order
    # releases the exact same held stock a supplier-declined one does.
    for item in order.items:
        if item.is_deleted:
            continue
        inventory = InventoryRepository.get_by_product_id(item.product_id)
        if inventory:
            InventoryRepository.reserve_quantity(inventory, -item.quantity)

    db.session.commit()

    publish_notification(
        build_order_cancelled_by_business_notification(
            order,
            supplier_user_id=str(supplier.supplier_id) if supplier else "",
            buyer_business_name=order.buyer_business_name or order.buyer_name or "A business",
        )
    )
    publish(
        AuditEvent(
            event_name=BusinessAuditEvent.ORDER_CANCELLED,
            domain=AuditDomain.BUSINESS,
            status=AuditStatus.SUCCESS,
            metadata={
                "business_id": str(business_id),
                "supplier_profile_id": str(supplier_profile_id),
                "order_id": str(order.id),
                "reason": reason,
            },
        )
    )

    return {
        "id": str(order.id),
        "orderReference": order.order_reference,
        "status": order.status.value,
    }
