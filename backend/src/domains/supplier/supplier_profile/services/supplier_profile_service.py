"""
supplier_profile's own service layer -- the first real write path this
domain has ever had. Everything before this was mock-only on the
frontend (see ProfileScreen.tsx's own docstring); this is what makes
it genuinely real.

COMPREHENSIVE, NOT NARROWLY SCOPED TO JUST THE NEW CONTACT FIELDS --
a deliberate choice made while building the "share your WhatsApp/
email/TikTok with connected businesses" feature: the SAME profile
screen already had other fields (business name, category, location,
description, photo visibility) that were quietly fake-saving. Building
a genuinely trustworthy "share your contact details" feature on a
screen where OTHER fields on the exact same form silently didn't save
would have undercut the whole point -- trust was the actual theme of
this work, not just three new database columns.
"""
from __future__ import annotations

import re
from typing import Optional
from uuid import UUID

from src.domains.supplier.supplier_profile.models.supplier_profile import (
    PhotoVisibility,
    SupplierProfile,
    VisibleImageSource,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.domains.supplier.supplier_profile.services.errors import ProfileValidationError
# The business-name rule is shared with supplier registration -- one
# definition in shared.validation.business_name. MAX_BUSINESS_NAME_LENGTH
# is re-exported through this import so existing references to
# supplier_profile_service.MAX_BUSINESS_NAME_LENGTH still resolve.
from src.shared.validation.business_name import (  # noqa: F401
    MAX_BUSINESS_NAME_LENGTH,
    normalize_business_name,
)
MAX_CATEGORY_LENGTH = 120
MAX_LOCATION_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 500
MAX_WHATSAPP_DIGITS = 15  # E.164's own real upper bound
MIN_WHATSAPP_DIGITS = 8
MAX_TIKTOK_HANDLE_LENGTH = 100
# R1,000,000 -- not a business rule so much as a mis-entry catch (a
# supplier typing rands into a cents field would otherwise sail
# through as a 100x minimum).
MAX_MINIMUM_ORDER_CENTS = 100_000_000

# TikTok's own real username rules -- letters, digits, underscore,
# period. Not enforcing TikTok's full ruleset (period can't be first/
# last, etc.) -- this is a courtesy check to catch an obviously wrong
# paste (a full URL, an @-mention with spaces), not a mirror of
# TikTok's own account-creation validation.
_TIKTOK_HANDLE_PATTERN = re.compile(r"^[A-Za-z0-9_.]+$")


def get_my_profile(supplier_id: str | UUID) -> SupplierProfile:
    """Real read path for the supplier's OWN full profile -- distinct
    from the business-facing get_supplier_profile in connections'
    own service, which returns a privacy-narrowed preview. This one
    returns everything, since the supplier is looking at their own
    record."""
    return SupplierProfileRepository.get_or_create_for_supplier(supplier_id)


def _normalize_whatsapp_number(raw: str) -> str:
    """Strips everything except digits -- the wa.me/ deep link the
    frontend builds from this needs bare international-format digits
    (country code included, no +, no spaces/dashes), so normalizing
    here once, at save time, means every reader downstream can trust
    the stored value is already in exactly that shape."""
    return re.sub(r"[^\d]", "", raw)


def _normalize_tiktok_handle(raw: str) -> str:
    """Strips a leading @ if present -- stored as a bare handle, same
    reasoning as WhatsApp above: the frontend builds the full
    tiktok.com/@<handle> URL from this, so normalizing once here means
    it never ends up double-@'d or inconsistently stored."""
    return raw.lstrip("@")


def update_my_profile(
    supplier_id: str | UUID,
    business_name: str,
    category: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    photo_visibility: Optional[str] = None,
    visible_image_source: Optional[str] = None,
    whatsapp_number: Optional[str] = None,
    contact_email: Optional[str] = None,
    tiktok_handle: Optional[str] = None,
    share_contact_details: bool = False,
    offers_delivery: Optional[bool] = None,
    minimum_order_cents: Optional[int] = None,
    collection_building: Optional[str] = None,
    collection_street: Optional[str] = None,
    collection_suburb: Optional[str] = None,
    collection_city: Optional[str] = None,
    collection_province: Optional[str] = None,
    collection_postal_code: Optional[str] = None,
    collection_latitude: Optional[float] = None,
    collection_longitude: Optional[float] = None,
) -> SupplierProfile:
    errors: list[str] = []

    try:
        business_name = normalize_business_name(business_name)
    except ValueError as exc:
        errors.extend(exc.args[0])

    if category is not None and len(category) > MAX_CATEGORY_LENGTH:
        errors.append(f"Category must be {MAX_CATEGORY_LENGTH} characters or fewer.")
    if location is not None and len(location) > MAX_LOCATION_LENGTH:
        errors.append(f"Location must be {MAX_LOCATION_LENGTH} characters or fewer.")
    if description is not None and len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer.")

    if photo_visibility is not None and photo_visibility not in [v.value for v in PhotoVisibility]:
        errors.append("Invalid photo visibility value.")
    if visible_image_source is not None and visible_image_source not in [v.value for v in VisibleImageSource]:
        errors.append("Invalid visible image source value.")

    normalized_whatsapp: Optional[str] = None
    if whatsapp_number is not None and whatsapp_number.strip():
        normalized_whatsapp = _normalize_whatsapp_number(whatsapp_number)
        if not (MIN_WHATSAPP_DIGITS <= len(normalized_whatsapp) <= MAX_WHATSAPP_DIGITS):
            errors.append("Enter a valid WhatsApp number, including country code.")

    normalized_tiktok: Optional[str] = None
    if tiktok_handle is not None and tiktok_handle.strip():
        normalized_tiktok = _normalize_tiktok_handle(tiktok_handle.strip())
        if len(normalized_tiktok) > MAX_TIKTOK_HANDLE_LENGTH or not _TIKTOK_HANDLE_PATTERN.match(normalized_tiktok):
            errors.append("Enter a valid TikTok handle (letters, numbers, underscores, and periods only).")

    # A minimum order must be a real, positive amount. NULL/absent
    # means "no minimum"; 0 or a negative number is not a minimum, it's
    # a mis-entry, and silently storing it would show a business
    # "Minimum order R0.00".
    if minimum_order_cents is not None and minimum_order_cents <= 0:
        errors.append("Minimum order must be more than R0, or left blank for no minimum.")
    if minimum_order_cents is not None and minimum_order_cents > MAX_MINIMUM_ORDER_CENTS:
        errors.append(f"Minimum order can't be more than R{MAX_MINIMUM_ORDER_CENTS // 100:,}.")

    if collection_latitude is not None and not (-90 <= collection_latitude <= 90):
        errors.append("Collection latitude is outside a valid range.")
    if collection_longitude is not None and not (-180 <= collection_longitude <= 180):
        errors.append("Collection longitude is outside a valid range.")

    if errors:
        raise ProfileValidationError("Check the highlighted fields.", errors=errors)

    profile = SupplierProfileRepository.get_or_create_for_supplier(supplier_id)

    update_fields: dict = {
        "business_name": business_name,
        "category": category.strip() if category else None,
        "location": location.strip() if location else None,
        "description": description.strip() if description else None,
        "whatsapp_number": normalized_whatsapp,
        "contact_email": contact_email.strip() if contact_email else None,
        "tiktok_handle": normalized_tiktok,
        "share_contact_details": share_contact_details,
        "offers_delivery": offers_delivery,
        "minimum_order_cents": minimum_order_cents,
        "collection_building": collection_building.strip() if collection_building else None,
        "collection_street": collection_street.strip() if collection_street else None,
        "collection_suburb": collection_suburb.strip() if collection_suburb else None,
        "collection_city": collection_city.strip() if collection_city else None,
        "collection_province": collection_province.strip() if collection_province else None,
        "collection_postal_code": collection_postal_code.strip() if collection_postal_code else None,
        "collection_latitude": collection_latitude,
        "collection_longitude": collection_longitude,
    }
    if photo_visibility is not None:
        update_fields["photo_visibility"] = PhotoVisibility(photo_visibility)
    if visible_image_source is not None:
        update_fields["visible_image_source"] = VisibleImageSource(visible_image_source)

    return SupplierProfileRepository.update(profile, **update_fields)
