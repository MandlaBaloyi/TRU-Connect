"""
order_history_service -- viewing SUBMITTED orders. Deliberately
separate from cart_service.py (which only ever builds carts) and
checkout_service.py (which only ever submits them) -- viewing history
is a genuinely different concern from either.
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from src.domains.network.orders.errors import SupplierNotFoundError
from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)


def list_order_history(business_id: str | UUID, supplier_profile_id: str | UUID) -> List[dict]:
    """"Order History" -- every order this business has SUBMITTED to
    this one supplier, most recent first. A lightweight summary per
    order (not full line-item detail) -- this is a real history LIST,
    not a per-order detail view; keeping it light avoids resolving
    product names/images for every item of every past order just to
    render a scrollable list."""
    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    orders = StockOrderRepository.list_submitted_for_business_and_supplier(business_id, supplier_profile_id)
    return [
        {
            "id": str(order.id),
            "status": order.status.value,
            "totalCents": order.total_cents,
            "itemCount": len([i for i in order.items if not i.is_deleted]),
            "paymentMethod": order.payment_method.value if order.payment_method else None,
            "deliveryType": order.delivery_type.value if order.delivery_type else None,
            "submittedAt": order.updated_at.isoformat() if order.updated_at else None,
        }
        for order in orders
    ]
