"""
The connection LISTS -- Community tab, both roles.

get_my_connections is deliberately ONE function/route rather than two
role-locked mirrors like every other pair in this domain (search,
requests, invitations) -- an active connection is genuinely the SAME
relationship viewed from either side, not two different concepts, so
branching on the caller's own role here is more honest than
duplicating near-identical logic.

end_connection is the "Disconnect from this Supplier" action -- the
same row transitions ACTIVE -> ENDED, never deleted.
list_ended_connections is the "who have I disconnected from" view.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.domains.network.connections.models.connection_request import (
    ConnectionEndReason,
    ConnectionRequestStatus,
)
from src.domains.network.connections.repositories.connection_request_repository import (
    ConnectionRequestRepository,
)
from src.domains.network.connections.services._common import (
    _lookup_business_name,
    _lookup_business_profile,
    _lookup_business_profile_id,
    _lookup_user,
    _person_name,
    _resolve_supplier_profile_id,
    _resolve_visible_photo_url,
)
from src.domains.network.connections.services.errors import (
    ConnectionNotActiveError,
    ConnectionRequestNotFoundError,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)


def get_my_connections(user_id: str | UUID, user_role: str) -> list[dict]:
    # Every row here is an ACTIVE connection, so the photo-visibility
    # gate (_resolve_visible_photo_url) is evaluated with
    # is_active_connection=True -- a CONNECTIONS-scoped photo is meant
    # to be visible to exactly the people on this list.
    if user_role == "supplier":
        supplier_profile_id = _resolve_supplier_profile_id(user_id)
        requests = ConnectionRequestRepository.list_active_for_supplier_profile(supplier_profile_id)
        results = []
        for r in requests:
            business_profile = _lookup_business_profile(r.business_id)
            business_user = _lookup_user(r.business_id)
            photo_url = None
            if business_profile is not None:
                photo_url = _resolve_visible_photo_url(
                    business_profile,
                    personal_photo_url=business_user.profile_image_url if business_user else None,
                    is_active_connection=True,
                )
            results.append(
                _connection_summary(
                    r,
                    other_party_name=_lookup_business_name(r.business_id),
                    owner_name=_person_name(business_user),
                    # BusinessProfile.id, NOT r.business_id (a raw
                    # auth.users.id) -- confirmed against
                    # get_business_profile's own lookup: these are
                    # genuinely different values, and the frontend route
                    # this feeds (GET /businesses/<business_profile_id>)
                    # expects the profile id specifically.
                    other_party_id=_lookup_business_profile_id(r.business_id),
                    photo_url=photo_url,
                )
            )
        return results

    requests = ConnectionRequestRepository.list_active_for_business(user_id)
    results = []
    for r in requests:
        supplier_profile = SupplierProfileRepository.get_by_id(r.supplier_profile_id)
        name = supplier_profile.business_name if supplier_profile else "Unknown supplier"
        photo_url = None
        supplier_user = None
        if supplier_profile is not None:
            supplier_user = _lookup_user(supplier_profile.supplier_id)
            # Brand image first (the supplier's public shopfront,
            # ungated -- same call discovery_service.get_supplier_profile
            # makes), then fall back to whatever _resolve_visible_photo_url
            # allows for an active connection.
            photo_url = supplier_profile.business_image_url or _resolve_visible_photo_url(
                supplier_profile,
                personal_photo_url=supplier_user.profile_image_url if supplier_user else None,
                is_active_connection=True,
            )
        results.append(
            _connection_summary(
                r,
                other_party_name=name,
                owner_name=_person_name(supplier_user),
                other_party_id=str(r.supplier_profile_id),
                photo_url=photo_url,
            )
        )
    return results


def _connection_summary(
    request,
    *,
    other_party_name: str,
    other_party_id: Optional[str],
    photo_url: Optional[str] = None,
    owner_name: Optional[str] = None,
) -> dict:
    return {
        "id": str(request.id),
        # The OTHER party's own real profile id -- a
        # supplier_profile_id when viewed by a business, a
        # BusinessProfile.id when viewed by a supplier. Nullable: a
        # business's own profile can genuinely not exist yet in some
        # edge cases (see _lookup_business_profile_id), and a missing
        # id should mean "don't render this as tappable", never a
        # broken link.
        "other_party_id": other_party_id,
        "name": other_party_name,
        # The PERSON behind the business -- the supplier's owner name
        # when viewed by a business, the business owner's name when
        # viewed by a supplier. Shown as the second line of the
        # WhatsApp-inbox-style connection row, under the business name.
        # Genuinely null whenever no person name was given (owner name
        # is optional at supplier registration), in which case the row
        # renders as a single line rather than an empty one.
        "ownerName": owner_name,
        "connectedSince": request.updated_at.isoformat() if request.updated_at else None,
        # The other party's resolved avatar: a supplier's brand/personal
        # photo when viewed by a business, a business's photo when viewed
        # by a supplier. Null is the normal case (nobody's uploaded one /
        # not shared) -- the frontend falls back to an initials avatar.
        "photoUrl": photo_url,
    }


def end_connection(business_id: str | UUID, supplier_profile_id: str | UUID, reason: str, details: Optional[str]) -> dict:
    """The real "Disconnect from this Supplier" action -- the same
    row transitions ACTIVE -> ENDED (see ConnectionRequestStatus's own
    docstring on ENDED), it's never deleted. Vanishes from
    get_my_connections' own ACTIVE-only list the moment this commits;
    list_ended_connections below is the "who have I disconnected from"
    view.

    reason arrives as the schema-validated uppercase string
    (EndConnectionSchema's own validate.OneOf) -- [] member-name
    lookup, not () value lookup, since the schema validates against
    the member names ("FOUND_BETTER_SUPPLIER"), not the lowercase
    .value strings.
    """
    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    if not connection:
        raise ConnectionRequestNotFoundError("Connection not found.")
    if connection.status != ConnectionRequestStatus.ACTIVE:
        raise ConnectionNotActiveError("This connection isn't currently active.")

    ended = ConnectionRequestRepository.end_connection(connection, ConnectionEndReason[reason], details)
    return {"connectionStatus": ended.status.value.upper()}


def list_ended_connections(business_id: str | UUID) -> list[dict]:
    """The "who have I disconnected from" list -- Community tab's own
    overflow menu. Mirrors get_my_connections' own ACTIVE-branch shape
    (id, name, otherPartyId, connectedSince) plus the two fields
    unique to this list (endedReason, endedAt) -- a business asking
    "who did I disconnect and why" needs those, an active-connections
    list never did."""
    requests = ConnectionRequestRepository.list_ended_for_business(business_id)
    results = []
    for r in requests:
        supplier_profile = SupplierProfileRepository.get_by_id(r.supplier_profile_id)
        name = supplier_profile.business_name if supplier_profile else "Unknown supplier"
        results.append(
            {
                "id": str(r.id),
                "name": name,
                "otherPartyId": str(r.supplier_profile_id),
                "endedReason": r.ended_reason.value.upper() if r.ended_reason else None,
                "endedDetails": r.ended_details,
                "endedAt": r.updated_at.isoformat() if r.updated_at else None,
            }
        )
    return results
