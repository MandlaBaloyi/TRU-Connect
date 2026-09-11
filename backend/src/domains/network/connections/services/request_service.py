"""
The connection-request lifecycle, both directions.

CREATE / RETRY: request_connection (business initiates) and
request_connection_to_business (supplier initiates) both funnel a
pre-existing pair through _handle_existing_connection -- idempotent for
PENDING/ACTIVE, a real reconnect for ENDED, a rate-limited retry for
DECLINED.

INBOX: the mirror pair of "requests I owe an approval on" --
get_customer_requests/approve_request/decline_request (a supplier
seeing business-initiated requests) and
get_supplier_requests/approve_supplier_request/decline_supplier_request
(a business seeing supplier-initiated ones). Same shape, opposite
ownership scoping: the supplier side resolves through
_resolve_supplier_profile_id first; the business side scopes directly
on ConnectionRequest.business_id (already the business's own account
id).
"""
from __future__ import annotations

from uuid import UUID

from src.domains.network.connections.models.connection_request import (
    ConnectionInitiatorRole,
    ConnectionRequestStatus,
)
from src.domains.network.connections.notification_templates.connection_templates import (
    build_connection_accepted_notification,
    build_connection_request_notification,
)
from src.domains.network.connections.repositories.connection_request_repository import (
    ConnectionRequestRepository,
)
from src.domains.network.connections.services._common import (
    _resolve_business_display_name,
    _resolve_supplier_profile_id,
)
from src.domains.network.connections.services.errors import (
    BusinessNotFoundError,
    ConnectionRequestNotFoundError,
    RetryLimitExceededError,
    SupplierNotFoundError,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.shared.helpers.helpers import mask_email, mask_phone
from src.shared.notifications.notifications import publish_notification


def _handle_existing_connection(
    existing, business_id: str | UUID, supplier_profile_id: str | UUID, initiated_by_role: ConnectionInitiatorRole
) -> dict:
    """Shared by request_connection and request_connection_to_business
    for what happens when a ConnectionRequest already exists between
    this business/supplier pair.

    PENDING/ACTIVE: fully idempotent -- a double-tap or a retried
    request after a flaky connection should never create a second row
    or surface an error for doing the same thing twice.

    ENDED: NOT simply idempotent -- a REAL BUG, found and fixed after
    direct report: this case fell through to the generic "just return
    the existing status" branch, meaning a reconnect attempt after a
    voluntary disconnect got a 200 response with the row never
    actually changing -- it stayed stuck at ENDED forever, invisible
    to every list that filters on PENDING/ACTIVE. Now resets to PENDING
    via ConnectionRequestRepository.reconnect, with no rate limiting
    (see that method's own docstring: ending a connection is
    voluntary, not an adversarial rejection).

    DECLINED: NOT simply idempotent -- attempts a real retry, subject
    to MAX_CONNECTION_RETRY_PER_DAY/_PER_WEEK. Fetches the row LOCKED
    before checking eligibility so there's no race window between "is
    this allowed" and "do it". Both windows are checked independently
    against the SAME retry_history; a retry only succeeds if it clears
    BOTH. When blocked, the raised error carries exactly when the NEXT
    retry becomes allowed.
    """
    if existing.status == ConnectionRequestStatus.ENDED:
        reconnected = ConnectionRequestRepository.reconnect(existing, initiated_by_role)
        return {"connectionStatus": reconnected.status.value.upper()}

    if existing.status != ConnectionRequestStatus.DECLINED:
        return {"connectionStatus": existing.status.value.upper()}

    from datetime import datetime, timedelta, timezone

    from flask import current_app

    from src.shared.constants.constants import MAX_CONNECTION_RETRY_PER_DAY, MAX_CONNECTION_RETRY_PER_WEEK

    locked = ConnectionRequestRepository.get_for_business_and_supplier_locked(business_id, supplier_profile_id)
    now = datetime.now(timezone.utc)
    day_window_start = now - timedelta(days=1)
    week_window_start = now - timedelta(days=7)

    retries_today = [t for t in locked.retry_history if t >= day_window_start]
    retries_this_week = [t for t in locked.retry_history if t >= week_window_start]

    max_per_day = current_app.config.get("MAX_CONNECTION_RETRY_PER_DAY", MAX_CONNECTION_RETRY_PER_DAY)
    max_per_week = current_app.config.get("MAX_CONNECTION_RETRY_PER_WEEK", MAX_CONNECTION_RETRY_PER_WEEK)

    day_blocked = len(retries_today) >= max_per_day
    week_blocked = len(retries_this_week) >= max_per_week

    if day_blocked or week_blocked:
        candidates = []
        if day_blocked:
            candidates.append(min(retries_today) + timedelta(days=1))
        if week_blocked:
            candidates.append(min(retries_this_week) + timedelta(days=7))
        next_retry_at = max(candidates)
        raise RetryLimitExceededError(
            "You've reached the limit for retrying this connection request.",
            data={"nextRetryAt": next_retry_at.isoformat()},
        )

    updated = ConnectionRequestRepository.retry(locked, initiated_by_role, now)
    return {"connectionStatus": updated.status.value.upper()}


def request_connection(business_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    supplier = SupplierProfileRepository.get_visible_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    existing = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    if existing:
        return _handle_existing_connection(
            existing, business_id, supplier_profile_id, ConnectionInitiatorRole.BUSINESS
        )

    request = ConnectionRequestRepository.create(
        business_id, supplier_profile_id, initiated_by_role=ConnectionInitiatorRole.BUSINESS
    )
    publish_notification(
        build_connection_request_notification(
            recipient_user_id=str(supplier.supplier_id),
            requester_name=_resolve_business_display_name(business_id),
            related_entity_id=str(request.id),
        )
    )
    return {"connectionStatus": request.status.value.upper()}


def request_connection_to_business(supplier_id: str | UUID, business_profile_id: str | UUID) -> dict:
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    business_profile = BusinessProfileRepository.get_by_id(business_profile_id)
    if not business_profile:
        raise BusinessNotFoundError("Business not found.")

    supplier_profile_id = _resolve_supplier_profile_id(supplier_id)
    existing = ConnectionRequestRepository.get_for_business_and_supplier(
        business_profile.business_id, supplier_profile_id
    )
    if existing:
        return _handle_existing_connection(
            existing, business_profile.business_id, supplier_profile_id, ConnectionInitiatorRole.SUPPLIER
        )

    request = ConnectionRequestRepository.create(
        business_profile.business_id, supplier_profile_id, initiated_by_role=ConnectionInitiatorRole.SUPPLIER
    )
    supplier_profile = SupplierProfileRepository.get_by_id(supplier_profile_id)
    publish_notification(
        build_connection_request_notification(
            recipient_user_id=str(business_profile.business_id),
            requester_name=supplier_profile.business_name if supplier_profile else "A supplier",
            related_entity_id=str(request.id),
        )
    )
    return {"connectionStatus": request.status.value.upper()}


# ---------------------------------------------------------------------------
# Supplier-side inbox: Customer Requests -- BUSINESS-initiated requests
# the supplier owes an approval on. file.txt Phase 3.
#
# supplier_id here is the authenticated caller's own account id (JWT
# identity, role=SUPPLIER) -- resolved to their SupplierProfile.id via
# _resolve_supplier_profile_id before ever touching ConnectionRequest.
# ---------------------------------------------------------------------------


def get_customer_requests(supplier_id: str | UUID) -> list[dict]:
    supplier_profile_id = _resolve_supplier_profile_id(supplier_id)
    requests = ConnectionRequestRepository.list_pending_for_supplier_profile(supplier_profile_id)

    results = []
    for request in requests:
        from src.domains.business.business_profile.repositories.business_profile_repository import (
            BusinessProfileRepository,
        )

        business_profile = BusinessProfileRepository.get_for_business(request.business_id)
        business_name = business_profile.business_name if business_profile else "Unknown business"

        results.append(
            {
                "id": str(request.id),
                "businessName": business_name,
                "requestedAt": request.created_at.isoformat() if request.created_at else None,
                "status": request.status.value.upper(),
            }
        )
    return results


def get_customer_request_detail(supplier_id: str | UUID, request_id: str | UUID) -> dict:
    supplier_profile_id = _resolve_supplier_profile_id(supplier_id)
    request = ConnectionRequestRepository.get_by_id_and_supplier_profile(request_id, supplier_profile_id)
    if request is None:
        raise ConnectionRequestNotFoundError("Request not found.")

    from src.domains.auth.repositories.user_repository import UserRepository
    from src.domains.business.business_profile.services.business_profile_service import BusinessProfileService

    profile = BusinessProfileService.get_profile(request.business_id)
    business_user = UserRepository.get_by_id(request.business_id)

    owner_name = None
    if business_user:
        owner_name = " ".join(filter(None, [business_user.first_name, business_user.last_name])) or None

    contact = profile.get("contactDetails", {})
    masked_phone = mask_phone(contact["phone"]) if contact.get("phone") else None
    masked_email = mask_email(contact["email"]) if contact.get("email") else None

    return {
        "id": str(request.id),
        "businessName": profile.get("businessDetails", {}).get("businessName") or (owner_name or "Unknown business"),
        "ownerName": owner_name,
        "category": profile.get("businessDetails", {}).get("category"),
        "location": profile.get("location", {}).get("cityOrTown"),
        "maskedPhone": masked_phone,
        "maskedEmail": masked_email,
        "requestedAt": request.created_at.isoformat() if request.created_at else None,
        "status": request.status.value.upper(),
    }


def approve_request(supplier_id: str | UUID, request_id: str | UUID) -> dict:
    supplier_profile_id = _resolve_supplier_profile_id(supplier_id)
    request = ConnectionRequestRepository.get_by_id_and_supplier_profile(request_id, supplier_profile_id)
    if request is None:
        raise ConnectionRequestNotFoundError("Request not found.")

    if request.status != ConnectionRequestStatus.ACTIVE:
        request = ConnectionRequestRepository.set_status(request, ConnectionRequestStatus.ACTIVE)
        supplier_profile = SupplierProfileRepository.get_by_id(supplier_profile_id)
        publish_notification(
            build_connection_accepted_notification(
                recipient_user_id=str(request.business_id),
                accepter_name=supplier_profile.business_name if supplier_profile else "The supplier",
                related_entity_id=str(request.id),
            )
        )
    return {"status": request.status.value.upper()}


def decline_request(supplier_id: str | UUID, request_id: str | UUID) -> dict:
    supplier_profile_id = _resolve_supplier_profile_id(supplier_id)
    request = ConnectionRequestRepository.get_by_id_and_supplier_profile(request_id, supplier_profile_id)
    if request is None:
        raise ConnectionRequestNotFoundError("Request not found.")

    if request.status != ConnectionRequestStatus.DECLINED:
        request = ConnectionRequestRepository.set_status(request, ConnectionRequestStatus.DECLINED)
    return {"status": request.status.value.upper()}


# ---------------------------------------------------------------------------
# Business-side inbox: Supplier Requests -- the mirror of Customer
# Requests above. SUPPLIER-initiated requests the business owes an
# approval on (Find Business's own "connect" action). business_id here
# is the authenticated caller's own account id directly -- no profile
# indirection needed on this side.
# ---------------------------------------------------------------------------


def get_supplier_requests(business_id: str | UUID) -> list[dict]:
    requests = ConnectionRequestRepository.list_pending_for_business(business_id)

    results = []
    for request in requests:
        supplier_profile = SupplierProfileRepository.get_by_id(request.supplier_profile_id)
        business_name = supplier_profile.business_name if supplier_profile else "Unknown supplier"

        results.append(
            {
                "id": str(request.id),
                "businessName": business_name,
                "requestedAt": request.created_at.isoformat() if request.created_at else None,
                "status": request.status.value.upper(),
            }
        )
    return results


def get_supplier_request_detail(business_id: str | UUID, request_id: str | UUID) -> dict:
    request = ConnectionRequestRepository.get_by_id_and_business(request_id, business_id)
    if request is None:
        raise ConnectionRequestNotFoundError("Request not found.")

    supplier_profile = SupplierProfileRepository.get_by_id(request.supplier_profile_id)
    if supplier_profile is None:
        raise SupplierNotFoundError("Supplier not found.")

    from src.domains.auth.repositories.user_repository import UserRepository

    supplier_user = UserRepository.get_by_id(supplier_profile.supplier_id)
    owner_name = None
    if supplier_user:
        owner_name = " ".join(filter(None, [supplier_user.first_name, supplier_user.last_name])) or None

    masked_email = mask_email(supplier_profile.normalized_email) if supplier_profile.normalized_email else None
    masked_phone = mask_phone(supplier_profile.normalized_phone) if supplier_profile.normalized_phone else None

    return {
        "id": str(request.id),
        "businessName": supplier_profile.business_name,
        "ownerName": owner_name,
        "category": supplier_profile.category,
        "location": supplier_profile.location,
        "maskedPhone": masked_phone,
        "maskedEmail": masked_email,
        "requestedAt": request.created_at.isoformat() if request.created_at else None,
        "status": request.status.value.upper(),
    }


def approve_supplier_request(business_id: str | UUID, request_id: str | UUID) -> dict:
    request = ConnectionRequestRepository.get_by_id_and_business(request_id, business_id)
    if request is None:
        raise ConnectionRequestNotFoundError("Request not found.")

    if request.status != ConnectionRequestStatus.ACTIVE:
        request = ConnectionRequestRepository.set_status(request, ConnectionRequestStatus.ACTIVE)
        requester_supplier_profile = SupplierProfileRepository.get_by_id(request.supplier_profile_id)
        if requester_supplier_profile:
            publish_notification(
                build_connection_accepted_notification(
                    recipient_user_id=str(requester_supplier_profile.supplier_id),
                    accepter_name=_resolve_business_display_name(business_id),
                    related_entity_id=str(request.id),
                )
            )
    return {"status": request.status.value.upper()}


def decline_supplier_request(business_id: str | UUID, request_id: str | UUID) -> dict:
    request = ConnectionRequestRepository.get_by_id_and_business(request_id, business_id)
    if request is None:
        raise ConnectionRequestNotFoundError("Request not found.")

    if request.status != ConnectionRequestStatus.DECLINED:
        request = ConnectionRequestRepository.set_status(request, ConnectionRequestStatus.DECLINED)
    return {"status": request.status.value.upper()}
