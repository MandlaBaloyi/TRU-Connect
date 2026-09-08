"""
Whether a business may place an order with a supplier at all.

Agreed during architecture review, reconciling an earlier (wrong)
proposal that would have gated CONNECTION itself on supplier
verification. Verification doesn't functionally exist yet, so gating
connection on it would make every supplier permanently unconnectable.
The actual gate belongs one step later, on ORDERING, and depends on TWO
things: (1) an ACTIVE connection, and (2) the supplier having at least
one real product -- there is nothing to order from an empty catalogue.
"""
from __future__ import annotations

from uuid import UUID

from src.domains.network.connections.models.connection_request import ConnectionRequestStatus
from src.domains.network.connections.repositories.connection_request_repository import (
    ConnectionRequestRepository,
)
from src.domains.network.connections.services.errors import SupplierNotFoundError
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)


def can_place_order(business_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository

    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    is_connected = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    product_count = SupplierOfferRepository.count_for_supplier(supplier_profile_id)
    has_products = product_count > 0

    if is_connected and has_products:
        reason = None
    elif not is_connected:
        reason = "NOT_CONNECTED"
    else:
        reason = "SUPPLIER_HAS_NO_PRODUCTS"

    return {
        "canOrder": is_connected and has_products,
        "isConnected": is_connected,
        "hasProducts": has_products,
        "reason": reason,
    }
