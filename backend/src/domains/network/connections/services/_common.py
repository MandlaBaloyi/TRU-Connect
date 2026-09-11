"""
Shared internals for the connections service modules -- helpers used
across more than one concern (discovery / catalogue / requests /
invitations / connection lists / reports). Nothing public lives here;
each concern module owns its own public surface.

THE AUTHORIZATION PATTERN, same as loan_book_service.py: the caller's
own id comes from the route's JWT identity, is a required parameter on
every public function in this domain, and every connection-request
lookup goes through an ownership-scoped repository fetch -- ownership
baked into the fetch, never checked after the fact.

PRIVACY, file.txt §4: search never returns more than
{Supplier,Business}Profile.to_search_result_dict/to_profile_preview_dict
already narrow it to. This service adds nothing to those shapes.

SEARCH IS NAME/BUSINESS-NAME PREFIX ONLY, both directions. Phone/email
exact-match search was a real, working feature that was deliberately
REMOVED (not left dormant -- the repository methods behind it were
deleted too): even with the identifier masked in the response,
exact-match phone/email search lets someone probe many numbers/
addresses one at a time to learn who's registered, which has nothing
to do with an existing relationship (the entire premise file.txt §4
sets out -- TruConnect digitises relationships that already exist, it
isn't a discovery/enumeration tool).
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.domains.network.connections.services.errors import (
    InvalidSearchQueryError,
    SupplierNotFoundError,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)

MIN_QUERY_LENGTH = 2


def _resolve_supplier_profile_id(supplier_id: str | UUID) -> UUID:
    profile = SupplierProfileRepository.get_by_supplier_id(supplier_id)
    if profile is None:
        # Should not normally happen -- every verified supplier account
        # gets one automatically (auth/services/otp_service.py's own
        # _seed_supplier_profile). Defensive, not a silently-assumed
        # invariant.
        raise SupplierNotFoundError("Your supplier profile could not be found.")
    return profile.id


def _resolve_business_display_name(business_id: str | UUID) -> str:
    """business_name if a BusinessProfile exists, falling back to the
    account's own personal name -- same resolution order already
    established in get_customer_request_detail's own owner_name logic
    and checkout_service.py's own buyer_business_name/buyer_name
    fallback, reused here rather than reinvented a third time."""
    from src.domains.auth.repositories.user_repository import UserRepository
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    profile = BusinessProfileRepository.get_for_business(business_id)
    if profile and profile.business_name:
        return profile.business_name

    user = UserRepository.get_by_id(business_id)
    if user:
        name = " ".join(filter(None, [user.first_name, user.last_name]))
        if name:
            return name
    return "A business"


def _lookup_business_name(user_id: str | UUID) -> str:
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    profile = BusinessProfileRepository.get_for_business(user_id)
    return profile.business_name if profile else "A business"


def _lookup_business_profile_id(user_id: str | UUID) -> Optional[str]:
    """The real BusinessProfile.id, distinct from user_id -- see
    get_my_connections' own comment on other_party_id for why this
    matters. None in the genuine edge case where no BusinessProfile
    row exists yet for this user (mirrors _lookup_business_name's own
    "A business" fallback for the same case, just returning None
    instead of a placeholder string, since there's no id to fall back
    to)."""
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    profile = BusinessProfileRepository.get_for_business(user_id)
    return str(profile.id) if profile else None


def _lookup_supplier_name(user_id: str | UUID) -> str:
    profile = SupplierProfileRepository.get_by_supplier_id(user_id)
    return profile.business_name if profile else "A supplier"


def _lookup_business_profile(user_id: str | UUID):
    """The full BusinessProfile row (not just its name/id) -- the
    connection LIST needs its photo_visibility/visible_image_source/
    business_image_url to resolve an avatar via _resolve_visible_photo_url,
    the same way discovery_service already does for the profile-preview
    endpoints. None in the same edge case _lookup_business_profile_id
    returns None for."""
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    return BusinessProfileRepository.get_for_business(user_id)


def _lookup_user(user_id: str | UUID):
    """The auth.users row itself. Returns the ROW rather than one
    extracted field because the connection list needs TWO things off it
    per connection -- profile_image_url (for _resolve_visible_photo_url's
    personal_photo_url arg) and the person's own name -- and fetching
    the same row twice per list item to get them separately would double
    the query count for no reason."""
    from src.domains.auth.models.user import User

    return User.query.filter_by(id=user_id).first()


def _person_name(user) -> Optional[str]:
    """first + last, or None when neither is set. None is a REAL,
    expected state now, not a data gap: owner name became optional at
    supplier registration (a sole trader may only have a business
    name), so callers must render the absence gracefully rather than
    substituting a placeholder."""
    if user is None:
        return None
    name = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    return name or None


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


def _dispatch_search(query: str, repository, *, resolve_photo) -> List[dict]:
    """Shared dispatch logic for both directions -- `repository` is
    either SupplierProfileRepository or BusinessProfileRepository;
    both expose the identical search_by_name_prefix + to_search_result_dict
    contract (confirmed directly against both files, not assumed).

    NAME/BUSINESS-NAME PREFIX ONLY -- see this module's own docstring
    for why phone/email exact-match search was removed.

    matchedField/maskedMatchedIdentifier are GONE from the result shape
    entirely, not just always "NAME"/"" now -- once name is the only
    match kind, carrying two fields whose value never varies is dead
    weight. See to_search_result_dict's own docstring
    (supplier_profile.py / business_profile.py) for the simplified shape.

    resolve_photo(profile) -> str | None is injected by the caller
    (search_suppliers/search_businesses) rather than computed here,
    since it needs the SEARCHING user's own identity (to check
    connection status per result) -- this function only knows the
    query, not who's asking. Same resolution rule as the profile-preview
    endpoints (see _resolve_visible_photo_url)."""
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
