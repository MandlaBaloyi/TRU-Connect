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

from src.core.exceptions import ForbiddenError
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
from src.domains.network.orders.repositories.stock_order_repository import (
    StockOrderRepository,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.core.base_model import utcnow
from src.shared.algorithms import reorder_gap


def get_my_connections(user_id: str | UUID, user_role: str) -> list[dict]:
    # Every row here is an ACTIVE connection, so the photo-visibility
    # gate (_resolve_visible_photo_url) is evaluated with
    # is_active_connection=True -- a CONNECTIONS-scoped photo is meant
    # to be visible to exactly the people on this list.
    if user_role == "supplier":
        supplier_profile_id = _resolve_supplier_profile_id(user_id)
        requests = ConnectionRequestRepository.list_active_for_supplier_profile(supplier_profile_id)
        # TWO QUERIES FOR THE WHOLE LIST, not two per row.
        history = StockOrderRepository.order_dates_by_counterparty(
            supplier_profile_id=supplier_profile_id
        )
        open_orders = StockOrderRepository.open_orders_by_counterparty(
            supplier_profile_id=supplier_profile_id
        )
        now = utcnow()
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
                    trading=_trading_facts(
                        history.get(str(r.business_id)), open_orders.get(str(r.business_id)), now
                    ),
                )
            )
        return _as_ledger(results)

    # EXHAUSTIVE, not a fall-through. This was reached by anything that
    # was not "supplier", which silently meant "treat them as a
    # business". Harmless while two roles existed; wrong the moment a
    # staff account can hold a token. A read that returns an empty list
    # for the wrong reason is worse than an error, because nobody
    # investigates an empty list.
    if user_role != "business":
        raise ForbiddenError("Connections belong to a business or a supplier account.")

    requests = ConnectionRequestRepository.list_active_for_business(user_id)
    history = StockOrderRepository.order_dates_by_counterparty(business_id=user_id)
    open_orders = StockOrderRepository.open_orders_by_counterparty(business_id=user_id)
    now = utcnow()
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
                trading=_trading_facts(
                    history.get(str(r.supplier_profile_id)),
                    open_orders.get(str(r.supplier_profile_id)),
                    now,
                ),
            )
        )
    return _as_ledger(results)


def _connection_summary(
    request,
    *,
    other_party_name: str,
    other_party_id: Optional[str],
    photo_url: Optional[str] = None,
    owner_name: Optional[str] = None,
    trading: Optional[dict] = None,
) -> dict:
    return {
        # V2_04 2.3: MY CONNECTIONS IS A RELATIONSHIP LEDGER, NOT A
        # CONTACT LIST. Merged in rather than nested under a key so the
        # row stays flat for the list that renders it.
        **(trading or _trading_facts(None, None, utcnow())),
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


def _trading_facts(dates, open_order, now) -> dict:
    """What the two parties' order history says about this relationship.

    ALL FOUR VALUES CAN BE NULL AND OFTEN ARE. A connection that has
    never traded is the normal state right after connecting, and it must
    render as a plain row -- not as zeroes, and not as "overdue".
    reorder_gap refuses to call anything overdue without a pattern
    (MIN_ORDERS_FOR_A_PATTERN), so a single order never produces one.
    """
    pattern = reorder_gap.pattern_from(list(dates or []), now)
    return {
        "orderCount": pattern.order_count,
        "lastOrderAt": pattern.last_order_at.isoformat() if pattern.last_order_at else None,
        "typicalGapDays": (
            round(pattern.typical_gap_days, 1) if pattern.typical_gap_days is not None else None
        ),
        "isOverdue": pattern.is_overdue,
        "openOrder": (
            {
                "id": str(open_order.id),
                "status": open_order.status.value,
                "submittedAt": (
                    open_order.submitted_at.isoformat() if open_order.submitted_at else None
                ),
            }
            if open_order is not None
            else None
        ),
    }


def _as_ledger(rows: list[dict]) -> list[dict]:
    """Order by TRADING REALITY, not alphabetically (V2_04 2.3).

        open order first, then reorder-due, then recency.

    WHY THE SERVER SORTS AND NOT THE APP. The same ordering has to hold
    on both roles' Community tabs and in anything that later reads this
    endpoint; a rule duplicated in two clients drifts the first time one
    of them is edited. It is also the rule most likely to change -- the
    moment fulfilment states exist, "open" means more than it does now.

    NEVER-TRADED ROWS SINK, but they sink to the bottom rather than
    disappearing: a supplier you have connected to and not yet ordered
    from is a real relationship and is exactly who a nudge should be
    aimed at later.
    """

    def key(row: dict):
        last = row.get("lastOrderAt") or ""
        return (
            0 if row.get("openOrder") else 1,
            0 if row.get("isOverdue") else 1,
            # Descending recency: a later ISO timestamp must sort first,
            # and these are all UTC isoformat so string order is time
            # order. Reversed by negating the comparison below.
            _DESCENDING(last),
        )

    return sorted(rows, key=key)


class _DESCENDING:
    """Sorts strings in reverse inside an otherwise ascending tuple key."""

    __slots__ = ("value",)

    def __init__(self, value: str):
        self.value = value

    def __lt__(self, other: "_DESCENDING") -> bool:
        return self.value > other.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _DESCENDING) and self.value == other.value
