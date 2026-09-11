"""
Whether a business may place an order with a supplier at all.

V2 STEP 4 CHANGED THE FIRST CONDITION FROM MANDATORY TO OPT-IN. The
gate used to require an ACTIVE connection from everyone. It now requires
one only from suppliers who have asked for it
(SupplierProfile.requires_connection, default FALSE).

WHY CONNECTION STOPPED BEING A GATE
(docs/v2/V2_00_ARCHITECTURE_EVOLUTION section 2.3)

1. ORDER ACCEPT/DECLINE IS A STRICTLY BETTER CONTROL. It is
   per-transaction and carries far more information -- the supplier sees
   what is being ordered, how much, and where to, instead of approving
   an abstract future relationship.

2. AN INTEGRATED SUPPLIER STRUCTURALLY CANNOT USE IT. There is nobody
   sitting at their end to click approve on a connection request, which
   is exactly why this is a per-supplier capability and not a platform
   rule.

3. IT BLOCKED THE DISCOVERY MODEL ENTIRELY. Browsing was already open --
   catalog_service and the storefront services both say so -- and this
   was the last thing standing between the catalogue and a feed a
   business can actually buy from.

WHAT DID NOT HAPPEN: NOTHING WAS DELETED. Connection requests, approval,
decline and disconnect all still work, and the mobile app still calls
them. They simply stopped being compulsory. A small supplier who
genuinely wants to know who is buying before stock moves turns
requires_connection on and gets exactly the old behaviour.

THE SECOND CONDITION IS UNCHANGED: the supplier must have at least one
real product, because there is nothing to order from an empty catalogue.
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


def connection_requirement_met(business_id: str | UUID, supplier) -> bool:
    """Has this business satisfied whatever connection rule this supplier
    set -- which for almost every supplier is no rule at all.

    ONE DEFINITION, USED TWICE, and it exists because the rule was
    previously written out twice: once here and once inside
    checkout_service. Flipping only this file would have left the app
    telling a business "you can order" and then refusing at checkout
    with "send a connection request first" -- worse than the old
    behaviour, because it is incoherent rather than merely strict.

    Takes the supplier ROW, not an id: both callers have already loaded
    it, and re-fetching per call would add a query to every cart read.
    """
    if not supplier.requires_connection:
        return True

    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier.id)
    return connection is not None and connection.status == ConnectionRequestStatus.ACTIVE


def can_place_order(business_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository

    supplier = SupplierProfileRepository.get_visible_by_id(supplier_profile_id)
    if not supplier:
        # This lookup is new. The gate previously imported
        # SupplierProfileRepository without ever calling it, so a request
        # naming a supplier that does not exist reported
        # "SUPPLIER_HAS_NO_PRODUCTS" -- technically true and completely
        # unhelpful. Now it says so.
        raise SupplierNotFoundError("Supplier not found.")

    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    is_connected = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    # The flip. False for almost every supplier, which is the point.
    requires_connection = bool(supplier.requires_connection)
    connection_satisfied = connection_requirement_met(business_id, supplier)

    product_count = SupplierOfferRepository.count_for_supplier(supplier_profile_id)
    has_products = product_count > 0

    can_order = connection_satisfied and has_products

    if can_order:
        reason = None
    elif not connection_satisfied:
        # Kept ahead of SUPPLIER_HAS_NO_PRODUCTS, matching the previous
        # ordering: when a supplier has asked to approve buyers first,
        # that is the thing the business has to act on, and telling them
        # about an empty catalogue instead would send them nowhere.
        reason = "NOT_CONNECTED"
    else:
        reason = "SUPPLIER_HAS_NO_PRODUCTS"

    return {
        "canOrder": can_order,
        "isConnected": is_connected,
        "hasProducts": has_products,
        # NEW KEY, and additive on purpose -- the mobile app ignores
        # fields it does not know, so this cannot break the shipped
        # client. It exists so the UI can tell "you may just order" apart
        # from "this supplier approves buyers first", which are the same
        # isConnected=false to a client that cannot see this flag.
        "requiresConnection": requires_connection,
        "reason": reason,
    }
