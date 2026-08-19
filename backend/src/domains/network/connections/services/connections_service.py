"""
Network Discovery business operations -- file.txt Phase 1/2/3,
FILE2.txt's own "FIRST TARGET: SUPPLIER DISCOVERY", GENERALIZED to
both directions.

Originally business-only (a business searches/invites suppliers,
a supplier approves). Now symmetric: a supplier can search/invite
businesses too, and a business approves those the same way a supplier
approves business-initiated ones. The underlying relationship
(ConnectionRequest) and invitation mechanism (NetworkInvitation) are
shared by both directions -- see those models' own docstrings on
initiated_by_role / invited_role, the two facts that make the
symmetry possible without duplicating either table.

THE AUTHORIZATION PATTERN, same as loan_book_service.py: the caller's
own id comes from the route's JWT identity, is a required parameter on
every method here, and every connection-request lookup goes through
an ownership-scoped repository fetch -- ownership baked into the
fetch, never checked after the fact.

PRIVACY, file.txt §4: search never returns more than
{Supplier,Business}Profile.to_search_result_dict/to_profile_preview_dict
already narrow it to. This service adds nothing to those shapes.

SEARCH DISPATCH: name/business-name prefix matching only. Phone/email
exact-match search was REMOVED (see this function's own docstring) --
even with the identifier masked in the response, exact-match phone/
email search is an enumeration vector: someone could probe many
numbers/addresses one at a time to learn who's registered on the
platform at all, independent of any real relationship with them. Name
search doesn't have this property -- a name has to already be roughly
known, and prefix-only matching (never substring) still bounds how
much a single query can reveal.
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from src.domains.network.connections.models.connection_request import (
    ConnectionInitiatorRole,
    ConnectionRequestStatus,
)
from src.domains.network.connections.repositories.connection_request_repository import (
    ConnectionRequestRepository,
)
from src.domains.network.connections.services.errors import (
    BusinessNotFoundError,
    ConnectionRequestNotFoundError,
    InvalidSearchQueryError,
    RetryLimitExceededError,
    SupplierNotFoundError,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.extensions import db
from src.shared.helpers.helpers import mask_email, mask_phone
from src.shared.validation.identifiers import normalize_email

MIN_QUERY_LENGTH = 2


def _dispatch_search(query: str, repository, *, resolve_photo) -> List[dict]:
    """Shared dispatch logic for both directions -- `repository` is
    either SupplierProfileRepository or BusinessProfileRepository;
    both expose the identical search_by_name_prefix + to_search_result_dict
    contract (confirmed directly against both files before writing this,
    not assumed).

    NAME/BUSINESS-NAME ONLY, both roles -- phone/email exact-match
    search (previously the first two branches here) was deliberately
    removed. It was a real, working feature, not a bug -- but a
    privacy-sensitive design choice that shouldn't have shipped this
    way: even with the identifier masked in the response, exact-match
    phone/email search lets someone probe many numbers/addresses one
    at a time to learn who's registered, which has nothing to do with
    an existing relationship (the entire premise file.txt §4 sets out
    -- TRU Connect digitises relationships that already exist, it
    isn't a discovery/enumeration tool). Removed rather than left
    dormant: SupplierProfileRepository.search_by_phone/search_by_email
    and BusinessProfileRepository's equivalents had no other real
    caller anywhere in this codebase (confirmed by searching, not
    assumed) -- keeping exact-match phone/email lookup methods alive
    with zero legitimate callers is exactly the kind of dead capability
    that tends to get silently wired back in later, so they were
    deleted along with these branches, not just unused.

    matchedField/maskedMatchedIdentifier are GONE from the result shape
    entirely, not just always "NAME"/"" now -- once name is the only
    match kind, carrying two fields whose value never varies is dead
    weight on the wire and in every type/mock that has to keep them in
    sync for no reason. See to_search_result_dict's own docstring
    (supplier_profile.py / business_profile.py) for the simplified
    shape.

    resolve_photo(profile) -> str | None is injected by the caller
    (search_suppliers/search_businesses) rather than computed here,
    since it needs the SEARCHING user's own identity (to check
    connection status per result) -- this function only knows the
    query, not who's asking. Same resolution rule as the profile-preview
    endpoints (see _resolve_visible_photo_url) -- NOBODY/CONNECTIONS-
    not-yet-active still correctly show nothing; only EVERYONE (or an
    active CONNECTIONS relationship) actually shows anything here, same
    as everywhere else this rule applies.
    """
    trimmed = query.strip()
    if len(trimmed) < MIN_QUERY_LENGTH:
        raise InvalidSearchQueryError(f"Search query must be at least {MIN_QUERY_LENGTH} characters.")

    profiles = repository.search_by_name_prefix(trimmed)
    results = []
    for profile in profiles:
        result = profile.to_search_result_dict()
        result["photoUrl"] = resolve_photo(profile)
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# Business searches Suppliers -- Find Supplier, the original direction.
# ---------------------------------------------------------------------------


def search_suppliers(query: str, business_id: str | UUID) -> List[dict]:
    from src.domains.auth.models.user import User

    def resolve_photo(supplier_profile) -> str | None:
        connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile.id)
        is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE
        supplier_user = User.query.filter_by(id=supplier_profile.supplier_id).first()
        personal_photo_url = supplier_user.profile_image_url if supplier_user else None
        return _resolve_visible_photo_url(
            supplier_profile, personal_photo_url=personal_photo_url, is_active_connection=is_active
        )

    return _dispatch_search(query, SupplierProfileRepository, resolve_photo=resolve_photo)


def _resolve_visible_photo_url(profile, *, personal_photo_url: str | None, is_active_connection: bool) -> str | None:
    """Shared by get_supplier_profile and get_business_profile --
    identical resolution rule for either role, since profile is
    whichever of SupplierProfile/BusinessProfile is being viewed and
    both now carry the exact same three fields (see their own model
    docstrings). Nothing shows unless BOTH the visibility gate AND a
    real chosen source agree -- NOBODY always hides regardless of
    connection; CONNECTIONS hides unless the connection is genuinely
    ACTIVE; NONE (the default) hides even under EVERYONE, since
    nobody has actively chosen a photo to show yet."""
    if profile.photo_visibility.value == "nobody":
        return None
    if profile.photo_visibility.value == "connections" and not is_active_connection:
        return None

    if profile.visible_image_source.value == "personal":
        return personal_photo_url
    if profile.visible_image_source.value == "business":
        return profile.business_image_url
    return None


def get_supplier_profile(business_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    from src.domains.auth.models.user import User
    from src.domains.supplier.catalogue.repositories.product_repository import ProductRepository

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    connection_status = connection.status.value.upper() if connection else "NOT_REQUESTED"
    is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    supplier_user = User.query.filter_by(id=supplier.supplier_id).first()
    personal_photo_url = supplier_user.profile_image_url if supplier_user else None
    visible_photo_url = _resolve_visible_photo_url(
        supplier, personal_photo_url=personal_photo_url, is_active_connection=is_active
    )

    profile = supplier.to_profile_preview_dict(connection_status, visible_photo_url)
    profile["productCount"] = ProductRepository.count_for_supplier(supplier_profile_id)
    return profile


def list_supplier_products(supplier_profile_id: str | UUID) -> List[dict]:
    """Real, minimal -- a name-only list, matching Product's own
    deliberately lean shape (see that model's docstring). Viewable by
    ANY authenticated business regardless of connection status --
    browsing stays open; only ordering is gated (can_place_order
    above)."""
    from src.domains.supplier.catalogue.repositories.product_repository import ProductRepository

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    products = ProductRepository.list_for_supplier(supplier_profile_id)
    return [{"id": str(p.id), "name": p.name} for p in products]


def _handle_existing_connection(
    existing, business_id: str | UUID, supplier_profile_id: str | UUID, initiated_by_role: ConnectionInitiatorRole
) -> dict:
    """Shared by request_connection and request_connection_to_business
    for what happens when a ConnectionRequest already exists between
    this business/supplier pair.

    PENDING/ACTIVE: still fully idempotent -- a double-tap or a
    retried request after a flaky connection should never create a
    second row or surface an error for doing the same thing twice.

    DECLINED: NOT simply idempotent -- attempts a real retry, subject
    to MAX_CONNECTION_RETRY_PER_DAY/_PER_WEEK. Fetches the row LOCKED
    (get_for_business_and_supplier_locked) before checking eligibility
    so there's no race window between "is this allowed" and "do it" --
    without the lock, two near-simultaneous retries could both read
    the same retry_history, both conclude they're within the limit,
    and both succeed, silently exceeding it.

    Both windows are checked independently against the SAME
    retry_history; a retry only succeeds if it clears BOTH. When
    blocked, the raised error carries exactly when the NEXT retry
    becomes allowed (whichever window's oldest qualifying attempt
    clears last -- both limits must be satisfied, not just one).
    """
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
    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
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
    return {"connectionStatus": request.status.value.upper()}


# ---------------------------------------------------------------------------
# Supplier searches Businesses -- Find Business, the reverse direction.
# Model/repository layer (BusinessProfile.normalized_phone/normalized_email,
# BusinessProfileRepository.search_by_*) was already built anticipating
# this; only this service layer and the routes are new.
# ---------------------------------------------------------------------------


def search_businesses(query: str, supplier_id: str | UUID) -> List[dict]:
    from src.domains.auth.models.user import User
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    supplier_profile_id = _resolve_supplier_profile_id(supplier_id)

    def resolve_photo(business_profile) -> str | None:
        connection = ConnectionRequestRepository.get_for_business_and_supplier(
            business_profile.business_id, supplier_profile_id
        )
        is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE
        business_user = User.query.filter_by(id=business_profile.business_id).first()
        personal_photo_url = business_user.profile_image_url if business_user else None
        return _resolve_visible_photo_url(
            business_profile, personal_photo_url=personal_photo_url, is_active_connection=is_active
        )

    return _dispatch_search(query, BusinessProfileRepository, resolve_photo=resolve_photo)


def get_business_profile(supplier_id: str | UUID, business_profile_id: str | UUID) -> dict:
    from src.domains.auth.models.user import User
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    business_profile = BusinessProfileRepository.get_by_id(business_profile_id)
    if not business_profile:
        raise BusinessNotFoundError("Business not found.")

    supplier_profile_id = _resolve_supplier_profile_id(supplier_id)
    connection = ConnectionRequestRepository.get_for_business_and_supplier(
        business_profile.business_id, supplier_profile_id
    )
    connection_status = connection.status.value.upper() if connection else "NOT_REQUESTED"
    is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    business_user = User.query.filter_by(id=business_profile.business_id).first()
    personal_photo_url = business_user.profile_image_url if business_user else None
    visible_photo_url = _resolve_visible_photo_url(
        business_profile, personal_photo_url=personal_photo_url, is_active_connection=is_active
    )

    return business_profile.to_profile_preview_dict(connection_status, visible_photo_url)


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
    return {"connectionStatus": request.status.value.upper()}


# ---------------------------------------------------------------------------
# Supplier-side: Customer Requests -- BUSINESS-initiated requests the
# supplier owes an approval on. file.txt Phase 3 / FILE2.txt "PHASE 3
# -- SUPPLIER APPROVAL".
#
# supplier_id here is the authenticated caller's own account id (JWT
# identity, role=SUPPLIER) -- resolved to their SupplierProfile.id via
# _resolve_supplier_profile_id before ever touching ConnectionRequest.
# ---------------------------------------------------------------------------


def _resolve_supplier_profile_id(supplier_id: str | UUID) -> UUID:
    profile = SupplierProfileRepository.get_by_supplier_id(supplier_id)
    if profile is None:
        # Should not normally happen -- every verified supplier account
        # gets one automatically (auth/services/otp_service.py's own
        # _seed_supplier_profile). Defensive, not a silently-assumed
        # invariant.
        raise SupplierNotFoundError("Your supplier profile could not be found.")
    return profile.id


def get_customer_requests(supplier_id: str | UUID) -> List[dict]:
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
# Business-side: Supplier Requests -- the mirror of Customer Requests
# above. SUPPLIER-initiated requests the business owes an approval on
# (Find Business's own "connect" action). business_id here is the
# authenticated caller's own account id directly -- no profile
# indirection needed on this side, ConnectionRequest.business_id
# already IS the business's own account id.
# ---------------------------------------------------------------------------


def get_supplier_requests(business_id: str | UUID) -> List[dict]:
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
    return {"status": request.status.value.upper()}


def decline_supplier_request(business_id: str | UUID, request_id: str | UUID) -> dict:
    request = ConnectionRequestRepository.get_by_id_and_business(request_id, business_id)
    if request is None:
        raise ConnectionRequestNotFoundError("Request not found.")

    if request.status != ConnectionRequestStatus.DECLINED:
        request = ConnectionRequestRepository.set_status(request, ConnectionRequestStatus.DECLINED)
    return {"status": request.status.value.upper()}


# ---------------------------------------------------------------------------
# Network Invitation -- file.txt Phase 2, GENERALIZED to both
# directions. Reuses src.shared.tickets.tickets directly and the
# already-existing supplier_invitation.html template for the
# business-invites-supplier direction; the reverse direction needs its
# own template (business_invitation.html), added alongside this.
#
# TWO-STAGE LINKING: link_invitation_at_registration() runs from
# AuthService.register_supplier / register_business at RAW
# registration time -- but only ever links the invitation to the new
# (still-unverified) account, it never creates a ConnectionRequest.
# complete_invitations_for_user() runs from OTPService's verification-
# success hook -- THAT'S where the real ConnectionRequest gets
# created. See network_invitation.py's own docstring for why this
# split matters (the hard-delete/orphan-FK reasoning).
# ---------------------------------------------------------------------------


def invite_supplier(business_id: str | UUID, email: str) -> dict:
    from src.domains.network.connections.models.network_invitation import InvitedRole

    return _send_invitation(
        inviter_id=business_id,
        invited_role=InvitedRole.SUPPLIER,
        email=email,
        rate_limit_prefix="supplier_invitation",
        template_name="supplier/supplier_invitation.html",
        inviter_name_lookup=_lookup_business_name,
    )


def invite_business(supplier_id: str | UUID, email: str) -> dict:
    from src.domains.network.connections.models.network_invitation import InvitedRole

    return _send_invitation(
        inviter_id=supplier_id,
        invited_role=InvitedRole.BUSINESS,
        email=email,
        rate_limit_prefix="business_invitation",
        template_name="business/business_invitation.html",
        inviter_name_lookup=_lookup_supplier_name,
    )


def _lookup_business_name(user_id: str | UUID) -> str:
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    profile = BusinessProfileRepository.get_for_business(user_id)
    return profile.business_name if profile else "A business"


def _lookup_supplier_name(user_id: str | UUID) -> str:
    profile = SupplierProfileRepository.get_by_supplier_id(user_id)
    return profile.business_name if profile else "A supplier"


def _send_invitation(
    inviter_id, invited_role, email: str, rate_limit_prefix: str, template_name: str, inviter_name_lookup
) -> dict:
    """Rate-limiting happens at the EMAIL layer (EmailService.send_template's
    own rate_limit_key/max), same as every other outbound email in this
    codebase -- not duplicated here."""
    from flask import current_app

    from src.domains.network.connections.repositories.network_invitation_repository import (
        NetworkInvitationRepository,
    )
    from src.shared.constants.constants import (
        DEFAULT_SUPPLIER_INVITATION_EXPIRY_HOURS,
        MAX_SUPPLIER_INVITATIONS_PER_HOUR,
    )
    from src.shared.email.email import EmailService
    from src.shared.tickets.tickets import create_ticket, hash_ticket, ticket_expiry

    normalized = normalize_email(email)

    expiry_hours = current_app.config.get(
        "SUPPLIER_INVITATION_EXPIRY_HOURS", DEFAULT_SUPPLIER_INVITATION_EXPIRY_HOURS
    )
    raw_ticket = create_ticket()
    expires_at = ticket_expiry(hours=expiry_hours)
    NetworkInvitationRepository.create(
        inviter_id=inviter_id,
        invited_role=invited_role,
        invited_email=normalized,
        ticket_hash=hash_ticket(raw_ticket),
        expires_at=expires_at,
    )

    inviter_name = inviter_name_lookup(inviter_id)
    base_url = current_app.config.get("APP_BASE_URL", "http://localhost:5000")
    invitation_url = f"{base_url}/join?ticket={raw_ticket}"

    EmailService.send_template(
        to=normalized,
        template_name=template_name,
        subject=f"{inviter_name} invited you to TRU Connect",
        context={"inviter_business_name": inviter_name, "invitation_url": invitation_url},
        rate_limit_key=f"{rate_limit_prefix}:{inviter_id}",
        rate_limit_max=MAX_SUPPLIER_INVITATIONS_PER_HOUR,
        rate_limit_window_seconds=3600,
    )

    return {"status": "SENT"}


def link_invitation_at_registration(ticket: str, new_user_id: str | UUID, new_user_role: str) -> None:
    """Called from AuthService.register_supplier / register_business --
    registration time, NOT verification time. Silently no-ops for a
    missing/expired/already-used ticket, OR when the ticket's
    invited_role doesn't match the role actually being registered
    (e.g. someone registering as a business using a ticket meant for a
    future supplier) -- a mismatch here is a reason to skip the
    automatic linkage, never a reason to block someone from creating
    an account normally.
    """
    from src.domains.network.connections.repositories.network_invitation_repository import (
        NetworkInvitationRepository,
    )
    from src.shared.tickets.tickets import hash_ticket

    invitation = NetworkInvitationRepository.get_by_ticket_hash(hash_ticket(ticket))
    if invitation is None or not invitation.is_valid():
        return
    if invitation.invited_role.value != new_user_role:
        return
    NetworkInvitationRepository.mark_registered(invitation, new_user_id)


def complete_invitations_for_user(user_id: str | UUID, user_role: str) -> None:
    """Called from OTPService's verification-success hook. Never
    raises: a failure here must not block the account's actual,
    already-succeeded verification, same resilience rule the seed
    helpers follow (their caller wraps this in the same try/except).

    user_role determines which side of the ConnectionRequest the
    just-verified person becomes, and which side the ORIGINAL inviter
    was (always the complement) -- see network_invitation.py's own
    docstring.
    """
    from src.domains.network.connections.models.network_invitation import InvitedRole
    from src.domains.network.connections.repositories.network_invitation_repository import (
        NetworkInvitationRepository,
    )

    for invitation in NetworkInvitationRepository.get_pending_by_invited_user(user_id):
        if invitation.invited_role == InvitedRole.SUPPLIER:
            # A business invited a supplier -- the just-verified user
            # IS that supplier.
            supplier_profile_id = _resolve_supplier_profile_id(user_id)
            business_id = invitation.inviter_id
            initiator = ConnectionInitiatorRole.BUSINESS
        else:
            # A supplier invited a business -- the just-verified user
            # IS that business; the inviter is the supplier.
            supplier_profile_id = _resolve_supplier_profile_id(invitation.inviter_id)
            business_id = user_id
            initiator = ConnectionInitiatorRole.SUPPLIER

        existing = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
        if existing is None:
            ConnectionRequestRepository.create(business_id, supplier_profile_id, initiated_by_role=initiator)
        NetworkInvitationRepository.mark_completed(invitation)


def validate_invitation(ticket: str) -> bool:
    """Read-only check -- lets a registration screen reached via a
    deep link show "this invite has expired" immediately, before the
    person fills in a form. Mirrors PasswordResetService.validate_ticket
    exactly."""
    from src.domains.network.connections.repositories.network_invitation_repository import (
        NetworkInvitationRepository,
    )
    from src.shared.tickets.tickets import hash_ticket

    invitation = NetworkInvitationRepository.get_by_ticket_hash(hash_ticket(ticket))
    return invitation is not None and invitation.is_valid()


# ---------------------------------------------------------------------------
# My Connections -- Community tab, both roles. ACTIVE connections only,
# regardless of which side originally initiated. Deliberately ONE
# function/route rather than two role-locked mirrors like every other
# pair in this domain (search, requests, invitations) -- an active
# connection is genuinely the SAME relationship viewed from either
# side, not two different concepts, so branching on the caller's own
# role here is more honest than duplicating near-identical logic.
# ---------------------------------------------------------------------------


def get_my_connections(user_id: str | UUID, user_role: str) -> List[dict]:
    if user_role == "supplier":
        supplier_profile_id = _resolve_supplier_profile_id(user_id)
        requests = ConnectionRequestRepository.list_active_for_supplier_profile(supplier_profile_id)
        return [_connection_summary(r, other_party_name=_lookup_business_name(r.business_id)) for r in requests]

    requests = ConnectionRequestRepository.list_active_for_business(user_id)
    results = []
    for r in requests:
        supplier_profile = SupplierProfileRepository.get_by_id(r.supplier_profile_id)
        name = supplier_profile.business_name if supplier_profile else "Unknown supplier"
        results.append(_connection_summary(r, other_party_name=name))
    return results


def _connection_summary(request, *, other_party_name: str) -> dict:
    return {
        "id": str(request.id),
        "name": other_party_name,
        "connectedSince": request.updated_at.isoformat() if request.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Ordering gate -- agreed during architecture review, reconciling an
# earlier (wrong) proposal that would have gated CONNECTION itself on
# supplier verification. Verification doesn't functionally exist yet
# (see TrustVerificationStatus's own frontend note), so gating
# connection on it would make every supplier permanently
# unconnectable. The actual gate belongs one step later, on ORDERING,
# and depends on TWO things being true, not one:
#
#   1. An ACTIVE connection between this business and supplier.
#   2. The supplier having at least one real product -- logically,
#      there is nothing to order from an empty catalogue, confirmed
#      directly rather than assumed.
#
# Nothing calls this yet -- Stock Ordering doesn't exist as a feature
# -- but the check itself is real and tested now, not a placeholder
# for later. Reaches into supplier/catalogue's own repository for the
# product-count half, the same cross-domain-read pattern this service
# already uses for business_profile/supplier_profile.
# ---------------------------------------------------------------------------


def can_place_order(business_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    from src.domains.supplier.catalogue.repositories.product_repository import ProductRepository

    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    is_connected = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    product_count = ProductRepository.count_for_supplier(supplier_profile_id)
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


# ---------------------------------------------------------------------------
# Photo settings -- which image shows, and to whom. Shared route/
# function for both roles, same reasoning as get_my_connections: how a
# profile presents itself to the network is genuinely one concern, not
# two role-specific mirrors -- both SupplierProfile and BusinessProfile
# carry the identical three fields (see their own model docstrings).
# ---------------------------------------------------------------------------


def update_my_photo_settings(
    user_id: str | UUID,
    user_role: str,
    *,
    visible_image_source: str | None = None,
    photo_visibility: str | None = None,
) -> dict:
    """Only the fields actually provided get changed -- either
    parameter left as None leaves that setting untouched."""
    if user_role == "supplier":
        from src.domains.supplier.supplier_profile.models.supplier_profile import (
            PhotoVisibility,
            VisibleImageSource,
        )

        profile = SupplierProfileRepository.get_or_create_for_supplier(user_id)
    else:
        from src.domains.business.business_profile.models.business_profile import (
            PhotoVisibility,
            VisibleImageSource,
        )
        from src.domains.business.business_profile.repositories.business_profile_repository import (
            BusinessProfileRepository,
        )

        profile = BusinessProfileRepository.get_or_create_for_business(user_id)

    if visible_image_source is not None:
        profile.visible_image_source = VisibleImageSource(visible_image_source)
    if photo_visibility is not None:
        profile.photo_visibility = PhotoVisibility(photo_visibility)

    db.session.commit()

    return {
        "visibleImageSource": profile.visible_image_source.value,
        "photoVisibility": profile.photo_visibility.value,
    }
