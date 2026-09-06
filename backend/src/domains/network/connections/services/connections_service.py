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

import math
from typing import List, Optional
from uuid import UUID

from src.domains.network.connections.models.connection_request import (
    ConnectionEndReason,
    ConnectionInitiatorRole,
    ConnectionRequestStatus,
)
from src.domains.network.connections.notification_templates.connection_templates import (
    build_connection_accepted_notification,
    build_connection_request_notification,
)
from src.domains.network.connections.models.supplier_report import SupplierReportReason
from src.domains.network.connections.repositories.connection_request_repository import (
    ConnectionRequestRepository,
)
from src.domains.network.connections.repositories.supplier_report_repository import SupplierReportRepository
from src.domains.network.connections.services.errors import (
    BusinessNotFoundError,
    ConnectionNotActiveError,
    ConnectionRequestNotFoundError,
    InvalidCatalogQueryError,
    InvalidSearchQueryError,
    ProductNotFoundError,
    RetryLimitExceededError,
    SupplierNotFoundError,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.extensions import db
from src.shared.helpers.helpers import mask_email, mask_phone
from src.shared.notifications.notifications import publish_notification
from src.shared.validation.identifiers import normalize_email

MIN_QUERY_LENGTH = 2


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
    from src.domains.supplier.products.repositories.product_repository import ProductRepository

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

    # Same gate as list_supplier_products'/get_supplier_product's own
    # contact block -- is_active AND the supplier's own opt-in. Added
    # here specifically so a business viewing an order they can no
    # longer self-cancel (already CONFIRMED) has a real way to
    # actually reach the supplier, not a dead-end message.
    profile["contact"] = None
    if is_active and supplier.share_contact_details:
        profile["contact"] = {
            "whatsappNumber": supplier.whatsapp_number,
            "email": supplier.contact_email,
            "tiktokHandle": supplier.tiktok_handle,
        }

    # Gated by is_active ONLY -- deliberately NOT also behind
    # share_contact_details like whatsapp/email above. Those are
    # optional extra communication channels a supplier might not want
    # to hand out; a collection address is core functional
    # information an actively-connected business needs to actually
    # complete a COLLECT order, not a discretionary opt-in.
    profile["collectionAddress"] = None
    if is_active and (supplier.collection_street or supplier.collection_suburb):
        profile["collectionAddress"] = {
            "building": supplier.collection_building,
            "street": supplier.collection_street,
            "suburb": supplier.collection_suburb,
            "city": supplier.collection_city,
            "province": supplier.collection_province,
            "postalCode": supplier.collection_postal_code,
            "latitude": float(supplier.collection_latitude) if supplier.collection_latitude is not None else None,
            "longitude": float(supplier.collection_longitude) if supplier.collection_longitude is not None else None,
        }

    return profile


VALID_CATALOG_SORT_OPTIONS = {"NEWEST", "NAME_ASC", "PRICE_ASC", "PRICE_DESC"}
MAX_CATALOG_PAGE_SIZE = 50
DEFAULT_CATALOG_PAGE_SIZE = 20


def get_supplier_product_categories(supplier_profile_id: str | UUID) -> List[str]:
    """The real fix for a real bug caught during review: this used to
    be derived on the FRONTEND from whichever products happened to be
    on the currently-loaded page, which broke the moment pagination
    existed. A dedicated, cheap, direct query -- correct regardless of
    page/sort/filter, and fetched once by the frontend rather than
    recomputed on every page change (a supplier's own category set
    doesn't change just because the business viewing it turned a
    page)."""
    from src.domains.supplier.products.repositories.product_repository import ProductRepository

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    return ProductRepository.list_distinct_categories_for_supplier(supplier_profile_id)


def list_supplier_products(
    business_id: str | UUID,
    supplier_profile_id: str | UUID,
    page: int = 1,
    limit: int = DEFAULT_CATALOG_PAGE_SIZE,
    sort: str = "NEWEST",
    category: Optional[str] = None,
) -> dict:
    """Real, and now genuinely useful -- name/category/price/unit,
    matching Product's own grown shape (Phase 1: Products). Viewable by
    ANY authenticated business regardless of connection status --
    browsing stays open; only ordering is gated (can_place_order
    above). Archived products excluded.

    business_id -- so this can ALSO carry contact at the top level
    (same gating as get_supplier_product's own: an ACTIVE connection
    AND the supplier's own share_contact_details opt-in, both
    required), for the "Contact Supplier" menu item, which needs
    contact info without requiring a business to first pick one
    specific product.

    PAGE/LIMIT/SORT/CATEGORY ARE THE REAL "PROTECT THE API, AND SCALE"
    FIX -- a supplier with hundreds of products used to mean one
    request returning every single row (and every image URL) at once.
    Sort and category filter are applied HERE, server-side, before
    pagination -- not left to the frontend to slice client-side,
    because once results are paginated, a client-side filter could
    only ever see whatever's on the current page, silently missing
    real matches sitting on other pages. limit is hard-capped at
    MAX_CATALOG_PAGE_SIZE regardless of what's requested -- the actual
    enforcement that makes this a genuine API protection, not just a
    UI suggestion a client could ignore by asking for limit=10000.
    """
    from src.domains.supplier.products.repositories.product_repository import ProductRepository
    from src.domains.supplier.products.services import product_media_service

    if page < 1:
        raise InvalidCatalogQueryError("Page must be 1 or greater.")
    if limit < 1:
        raise InvalidCatalogQueryError("Limit must be 1 or greater.")
    limit = min(limit, MAX_CATALOG_PAGE_SIZE)
    if sort not in VALID_CATALOG_SORT_OPTIONS:
        raise InvalidCatalogQueryError(f"Invalid sort value. Must be one of: {', '.join(sorted(VALID_CATALOG_SORT_OPTIONS))}.")
    if category is not None:
        from src.domains.supplier.products.models.product import ProductCategory

        try:
            ProductCategory(category)
        except ValueError:
            raise InvalidCatalogQueryError("Invalid category value.")

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    contact = None
    if is_active and supplier.share_contact_details:
        contact = {
            "whatsappNumber": supplier.whatsapp_number,
            "email": supplier.contact_email,
            "tiktokHandle": supplier.tiktok_handle,
        }

    products, total_count = ProductRepository.list_for_supplier_paginated(
        supplier_profile_id, page=page, limit=limit, sort=sort, category=category
    )
    total_pages = max(1, math.ceil(total_count / limit))

    # supplierName sits at the TOP LEVEL, not repeated inside every
    # product dict -- same value for every row, so duplicating it
    # would just be wasted bytes on every response. Same "certainty"
    # fix as get_supplier_product's own supplierName, applied one
    # screen earlier in the same flow -- a business browsing the whole
    # catalogue should know whose it is before ever tapping into one
    # specific product, not just once they get there.
    return {
        "supplierName": supplier.business_name,
        "contact": contact,
        "page": page,
        "totalPages": total_pages,
        "totalCount": total_count,
        "products": _build_catalog_product_dicts(products),
    }


def _build_catalog_product_dicts(products: List) -> List[dict]:
    """Shared by list_supplier_products above and
    list_related_products below -- both need the exact same enriched
    shape (compareAtPriceCents, inStock, approved-only images), and
    duplicating this risks the two silently drifting apart over time.
    Batches the inventory lookup, not one query per product -- same
    "protect the API" discipline as pagination itself. A product with
    no matching inventory row is treated as zero available (the same
    default value a real row would have anyway), never created as a
    side effect of this read -- see InventoryRepository.
    list_by_product_ids' own docstring on why a business simply
    browsing must never trigger a write to the supplier's own
    inventory rows."""
    from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
    from src.domains.supplier.products.services import product_media_service

    inventory_rows = InventoryRepository.list_by_product_ids([p.id for p in products])
    available_by_product = {row.product_id: row.quantity_on_hand - row.quantity_reserved for row in inventory_rows}

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "category": p.category.value,
            "priceCents": p.price_cents,
            # Added so a business browsing this catalogue can see the
            # same "was RX, now RY" / "% OFF" badge the supplier
            # themselves sees on their own product screens -- the
            # underlying discount is real regardless of who's looking
            # at it.
            "compareAtPriceCents": p.compare_at_price_cents,
            "sellingUnit": p.selling_unit.value,
            # A real, direct answer to "can I actually order this
            # right now" -- never the exact quantity (a business
            # doesn't need to know "exactly 3 left", only whether
            # it's currently orderable at all; the supplier's own
            # exact count stays theirs).
            "inStock": available_by_product.get(p.id, 0) > 0,
            # Real, APPROVED-only media -- this is exactly the endpoint
            # a business actually sees, so it's the one place this
            # matters most (see product_media_service's own
            # list_approved_media docstring for why only APPROVED ever
            # reaches here).
            "images": product_media_service.list_approved_media(p.id),
        }
        for p in products
    ]


def list_related_products(business_id: str | UUID, supplier_profile_id: str | UUID, product_id: str | UUID) -> dict:
    """"More from [Supplier]" -- see ProductRepository.
    list_related_products' own docstring for the full backfill
    reasoning. Genuinely related (same category) products come first,
    then any other product from this same supplier fills the
    remaining slots if fewer than 5 genuine matches exist -- confirmed
    after direct feedback: a supplier with real stock spread across
    many categories was showing nothing here far too often. Priority
    always goes to real relatedness; backfill only ever fills leftover
    slots, never displaces a genuine match. Same visibility rule as
    browsing the rest of the catalogue -- viewable by any
    authenticated business regardless of connection status.
    """
    from src.domains.supplier.products.repositories.product_repository import ProductRepository

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product or product.is_archived:
        raise ProductNotFoundError("Product not found.")

    related = ProductRepository.list_related_products(supplier_profile_id, product.category, product.id, limit=5)
    return {"products": _build_catalog_product_dicts(related)}


def get_supplier_product(business_id: str | UUID, supplier_profile_id: str | UUID, product_id: str | UUID) -> dict:
    """The real, previously-missing piece confirmed during the My
    Connections/search UI review: list_supplier_products above lets a
    business see a supplier's whole catalogue, but there was no way at
    all to view ONE product in real detail -- the supplier's own
    product detail route is locked to role_required("supplier") plus
    an ownership check, so a business calling it would always be
    rejected outright, not just see the wrong data.

    Same visibility rules as list_supplier_products -- viewable by ANY
    authenticated business regardless of connection status (browsing
    stays open; only ordering is gated, see can_place_order), archived
    products excluded. get_by_id_and_supplier itself only filters
    is_deleted, not is_archived (it's shared with supplier-side
    mutation call sites that legitimately need to see archived rows),
    so the archived check happens here explicitly instead.

    ProductNotFoundError covers three cases identically -- genuinely
    doesn't exist, exists under a different supplier than the URL
    says, or exists but is archived -- same IDOR-safety reasoning as
    every other *NotFoundError in this domain: a business should never
    be able to tell these apart from the response.

    business_id IS NEW -- added specifically so the business viewing
    this can be CERTAIN who they're actually looking at (the real
    problem this whole feature solves: "how do I know this is
    genuinely my supplier before I order from them"). Two things this
    unlocks: the supplier's own real business name (never shown on
    this screen before), and their WhatsApp/email/TikTok, gated
    server-side on a genuinely ACTIVE connection -- never trusted from
    the app, same resolution pattern as _resolve_visible_photo_url
    already uses for photos. contact is null (not an empty object)
    whenever EITHER the connection isn't active OR the supplier hasn't
    opted into share_contact_details -- a business browsing without a
    real relationship should never be able to tell "not connected"
    apart from "connected but declined to share" from the response
    shape.
    """
    from src.domains.supplier.products.repositories.product_repository import ProductRepository
    from src.domains.supplier.products.services import product_media_service

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product or product.is_archived:
        raise ProductNotFoundError("Product not found.")

    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    contact = None
    if is_active and supplier.share_contact_details:
        contact = {
            "whatsappNumber": supplier.whatsapp_number,
            "email": supplier.contact_email,
            "tiktokHandle": supplier.tiktok_handle,
        }

    from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository

    inventory = InventoryRepository.get_by_product_id(product.id)
    available = (inventory.quantity_on_hand - inventory.quantity_reserved) if inventory else 0

    return {
        "id": str(product.id),
        "name": product.name,
        "supplierName": supplier.business_name,
        "contact": contact,
        "category": product.category.value,
        "priceCents": product.price_cents,
        "compareAtPriceCents": product.compare_at_price_cents,
        "sellingUnit": product.selling_unit.value,
        # Same real, direct answer as list_supplier_products' own
        # inStock -- never the exact quantity.
        "inStock": available > 0,
        "description": product.description,
        "sku": product.sku,
        "productCode": product.product_code,
        "images": product_media_service.list_approved_media(product.id),
    }


def _handle_existing_connection(
    existing, business_id: str | UUID, supplier_profile_id: str | UUID, initiated_by_role: ConnectionInitiatorRole
) -> dict:
    """Shared by request_connection and request_connection_to_business
    for what happens when a ConnectionRequest already exists between
    this business/supplier pair.

    PENDING/ACTIVE: still fully idempotent -- a double-tap or a
    retried request after a flaky connection should never create a
    second row or surface an error for doing the same thing twice.

    ENDED: NOT simply idempotent -- a REAL BUG, found and fixed after
    direct report: this case fell through to the generic "just return
    the existing status" branch below, meaning a reconnect attempt
    after a voluntary disconnect got a 200 response with the row never
    actually changing -- it stayed stuck at ENDED forever, invisible
    to every list that filters on PENDING/ACTIVE on both sides. Now
    resets to PENDING via ConnectionRequestRepository.reconnect, with
    no rate limiting (see that method's own docstring on why: ending a
    connection is voluntary, not an adversarial rejection, so
    DECLINED's own "guard against harassment" reasoning doesn't
    transfer here).

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
    publish_notification(
        build_connection_request_notification(
            recipient_user_id=str(supplier.supplier_id),
            requester_name=_resolve_business_display_name(business_id),
            related_entity_id=str(request.id),
        )
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
        return [
            _connection_summary(
                r,
                other_party_name=_lookup_business_name(r.business_id),
                # BusinessProfile.id, NOT r.business_id (a raw
                # auth.users.id) -- confirmed against
                # get_business_profile's own lookup: these are
                # genuinely different values, and the frontend route
                # this feeds (GET /businesses/<business_profile_id>)
                # expects the profile id specifically.
                other_party_id=_lookup_business_profile_id(r.business_id),
            )
            for r in requests
        ]

    requests = ConnectionRequestRepository.list_active_for_business(user_id)
    results = []
    for r in requests:
        supplier_profile = SupplierProfileRepository.get_by_id(r.supplier_profile_id)
        name = supplier_profile.business_name if supplier_profile else "Unknown supplier"
        results.append(
            _connection_summary(r, other_party_name=name, other_party_id=str(r.supplier_profile_id))
        )
    return results


def _connection_summary(request, *, other_party_name: str, other_party_id: Optional[str]) -> dict:
    return {
        "id": str(request.id),
        # The OTHER party's own real profile id -- a
        # supplier_profile_id when viewed by a business, a
        # BusinessProfile.id when viewed by a supplier. Same "one
        # field, meaning depends on who's asking, resolved
        # server-side" pattern as name just below. Nullable: a
        # business's own profile can genuinely not exist yet in some
        # edge cases (see _lookup_business_profile_id below), and a
        # missing id should mean "don't render this as tappable",
        # never a broken link. REAL GAP FOUND DURING the search/
        # connections UI review: without this field at all, a tapped
        # connection had no real id to route anywhere with -- only the
        # connection REQUEST's own id (this dict's own "id" field
        # above) was ever exposed.
        "other_party_id": other_party_id,
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
# for later. Reaches into supplier/products' own repository for the
# product-count half, the same cross-domain-read pattern this service
# already uses for business_profile/supplier_profile.
# ---------------------------------------------------------------------------


def can_place_order(business_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    from src.domains.supplier.products.repositories.product_repository import ProductRepository

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


def list_ended_connections(business_id: str | UUID) -> List[dict]:
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


def report_supplier(
    business_id: str | UUID,
    supplier_profile_id: str | UUID,
    reason: str,
    details: Optional[str],
    product_id: Optional[str | UUID] = None,
) -> dict:
    """A business reporting a concern about a supplier -- see
    SupplierReport's own model docstring on why this is a real,
    permanent record today even though no admin panel exists yet to
    review it, and why the notification email is a courtesy on top of
    that record, never a replacement for it. Deliberately does NOT
    require an active (or even any) connection -- a genuine scam
    concern should be reportable regardless of connection status,
    unlike ordering or seeing contact details, which both genuinely do
    require one.

    product_id IS OPTIONAL -- set when reported from a specific
    product's own 3-dot menu ("Report this product"), omitted when
    reported from the catalogue's own menu ("Report" the supplier
    generally). When provided, it's verified to genuinely belong to
    THIS supplier first -- same IDOR-safety discipline as every other
    ownership check in this domain; a mismatched product_id is
    silently dropped rather than trusted, so a report can never end up
    misleadingly attached to a product that isn't actually this
    supplier's.

    reason arrives as the schema-validated uppercase string
    (ReportSupplierSchema's own validate.OneOf) -- same [] member-name
    lookup reasoning as end_connection above.
    """
    from flask import current_app

    from src.domains.supplier.products.repositories.product_repository import ProductRepository
    from src.shared.email.email import EmailService

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    verified_product_id = None
    product_name = None
    if product_id is not None:
        product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
        if product:
            verified_product_id = product.id
            product_name = product.name

    report = SupplierReportRepository.create(
        business_id, supplier_profile_id, SupplierReportReason[reason], details, product_id=verified_product_id
    )

    reports_email = current_app.config.get("SUPPLIER_REPORTS_EMAIL")
    if reports_email:
        EmailService.send_template(
            to=reports_email,
            template_name="network/supplier_reported.html",
            subject=f"Supplier report: {supplier.business_name}",
            context={
                "supplier_business_name": supplier.business_name,
                "supplier_profile_id": str(supplier_profile_id),
                "product_name": product_name,
                "reason": report.reason.value.replace("_", " ").title(),
                "details": details or "(no additional details provided)",
                "report_id": str(report.id),
            },
        )

    return {"status": "SUBMITTED"}
