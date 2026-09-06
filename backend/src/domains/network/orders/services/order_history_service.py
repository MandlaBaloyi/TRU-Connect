"""
order_history_service -- viewing SUBMITTED orders. Deliberately
separate from cart_service.py (which only ever builds carts) and
checkout_service.py (which only ever submits them) -- viewing history
is a genuinely different concern from either.
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from src.domains.network.orders.errors import OrderNotFoundError, SupplierNotFoundError
from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.products.services import product_media_service
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.shared.audit.audit import publish
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditStatus
from src.shared.audit.event_types.business import BusinessAuditEvent


def list_order_history(business_id: str | UUID, supplier_profile_id: str | UUID) -> List[dict]:
    """"Order History" -- every order this business has SUBMITTED to
    this one supplier, most recent first. A lightweight summary per
    order (not full line-item detail) -- this is a real history LIST,
    not a per-order detail view; keeping it light avoids resolving
    product names/images for every item of every past order just to
    render a scrollable list.

    orderReference -- the real, human-facing reference (TRU-XXXX-XXXXXX),
    what's actually SHOWN on screen everywhere a person sees this
    list. `id` is also included, but purely as an internal navigation
    detail -- the frontend needs SOME way to know which order to
    fetch full detail for when a row is tapped, and this order's own
    id is already visible to (and owned by) the exact business asking
    for it, so including it here isn't exposing anything new. The
    real discipline is "never render the raw id on screen," not
    "never let the frontend know it exists."
    """
    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    orders = StockOrderRepository.list_submitted_for_business_and_supplier(business_id, supplier_profile_id)
    return [
        {
            "id": str(order.id),
            "orderReference": order.order_reference,
            "status": order.status.value,
            "totalCents": order.total_cents,
            "itemCount": len([i for i in order.items if not i.is_deleted]),
            "paymentMethod": order.payment_method.value if order.payment_method else None,
            "deliveryType": order.delivery_type.value if order.delivery_type else None,
            "submittedAt": order.submitted_at.isoformat() if order.submitted_at else None,
        }
        for order in orders
    ]


def get_order_detail(business_id: str | UUID, supplier_profile_id: str | UUID, order_id: str | UUID) -> dict:
    """Tapping into ONE specific past order from the history list --
    the real line-item detail list_order_history deliberately doesn't
    resolve (see that function's own docstring on why the list itself
    stays lightweight).

    Still looked up by the real internal id -- that's an
    implementation detail the frontend passes through from whichever
    history row was tapped, never meant to be typed by hand or shared
    outside the app; the order reference is what's meant for that.

    IDOR-safe by construction -- StockOrderRepository.
    get_by_id_for_business_and_supplier scopes the lookup by BOTH
    business_id and supplier_profile_id, not just the order's own id;
    a genuinely nonexistent order and one that exists but belongs to
    someone else are deliberately indistinguishable to the caller.

    THE REJECTION ITSELF IS AUDITED (BusinessAuditEvent.
    ORDER_ACCESS_DENIED) -- repeated attempts from the same account
    requesting order ids that aren't theirs is exactly the kind of
    security-relevant pattern worth being able to find later, same
    reasoning as checkout_service.py's own ORDER_LIMIT_EXCEEDED.

    Buyer details ARE included here (name, phone, email, business
    name) -- this is the one real, legitimate e-commerce order-detail
    view, exactly like Bash's/Takealot's own; a supplier acting on
    this order genuinely needs to know who placed it. The list view
    above deliberately doesn't repeat this for every row -- same
    "keep the list light" reasoning as not resolving item
    images/names there either.
    """
    order = StockOrderRepository.get_by_id_for_business_and_supplier(order_id, business_id, supplier_profile_id)
    if not order:
        publish(
            AuditEvent(
                event_name=BusinessAuditEvent.ORDER_ACCESS_DENIED,
                domain=AuditDomain.BUSINESS,
                status=AuditStatus.FAILURE,
                metadata={
                    "business_id": str(business_id),
                    "supplier_profile_id": str(supplier_profile_id),
                    "requested_order_id": str(order_id),
                },
            )
        )
        raise OrderNotFoundError("Order not found.")

    items = []
    for item in order.items:
        if item.is_deleted:
            continue
        # A product referenced by a historical order may since have
        # been archived or deleted -- still shown here (this order
        # genuinely contained it), never silently hidden, same
        # reasoning as cart_service's own isStale handling.
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
        "id": str(order.id),
        "orderReference": order.order_reference,
        "status": order.status.value,
        "totalCents": order.total_cents,
        "paymentMethod": order.payment_method.value if order.payment_method else None,
        "deliveryType": order.delivery_type.value if order.delivery_type else None,
        "deliveryAddressText": order.delivery_address_text,
        "submittedAt": order.submitted_at.isoformat() if order.submitted_at else None,
        "decidedAt": order.decided_at.isoformat() if order.decided_at else None,
        "buyerName": order.buyer_name,
        "buyerPhone": order.buyer_phone,
        "buyerEmail": order.buyer_email,
        "buyerBusinessName": order.buyer_business_name,
        # Only meaningful when status is DECLINED -- present (as None)
        # regardless of status rather than omitted, so the frontend's
        # type doesn't need an extra "was this key even sent" check on
        # top of "is it null".
        "declineReason": order.decline_reason,
        "declineDetails": order.decline_details,
        # Only meaningful when status is CANCELLED.
        "cancelledBy": order.cancelled_by,
        "cancelReason": order.cancel_reason,
        "cancelDetails": order.cancel_details,
        "cancelledAt": order.cancelled_at.isoformat() if order.cancelled_at else None,
        "items": items,
    }
