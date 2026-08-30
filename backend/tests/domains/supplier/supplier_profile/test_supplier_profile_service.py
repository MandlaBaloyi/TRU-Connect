"""
Tests for supplier_profile_service.py -- the first real write path
this domain has ever had. Everything before this was mock-only on the
frontend.
"""
from __future__ import annotations

import pytest

from src.domains.supplier.supplier_profile.models.supplier_profile import PhotoVisibility, VisibleImageSource
from src.domains.supplier.supplier_profile.services import supplier_profile_service
from src.domains.supplier.supplier_profile.services.errors import ProfileValidationError


def test_get_my_profile_creates_one_if_none_exists(make_supplier):
    """A brand-new supplier calling this for the very first time, before
    ever touching anything else, must still get a real profile back --
    never a 404."""
    supplier = make_supplier()

    profile = supplier_profile_service.get_my_profile(supplier.id)

    assert profile is not None
    assert profile.supplier_id == supplier.id


def test_update_my_profile_persists_business_name(make_supplier):
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(supplier.id, business_name="Real Wholesale Co")

    assert profile.business_name == "Real Wholesale Co"


def test_update_my_profile_rejects_blank_business_name(make_supplier):
    supplier = make_supplier()

    with pytest.raises(ProfileValidationError):
        supplier_profile_service.update_my_profile(supplier.id, business_name="   ")


def test_update_my_profile_persists_category_location_description(make_supplier):
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(
        supplier.id,
        business_name="Real Wholesale Co",
        category="Wholesale beverages",
        location="Polokwane",
        description="Bulk soft drinks and snacks.",
    )

    assert profile.category == "Wholesale beverages"
    assert profile.location == "Polokwane"
    assert profile.description == "Bulk soft drinks and snacks."


# --- The real new behaviour: contact fields -----------------------------


def test_update_my_profile_normalizes_a_formatted_whatsapp_number(make_supplier):
    """THE REAL BEHAVIOUR THIS FEATURE DEPENDS ON -- the frontend's own
    wa.me/ deep link needs bare international-format digits; a supplier
    typing a formatted number must have it normalized at save time, not
    stored as-typed."""
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(
        supplier.id, business_name="Co", whatsapp_number="+27 82 123 4567"
    )

    assert profile.whatsapp_number == "27821234567"


def test_update_my_profile_rejects_a_too_short_whatsapp_number(make_supplier):
    supplier = make_supplier()

    with pytest.raises(ProfileValidationError):
        supplier_profile_service.update_my_profile(supplier.id, business_name="Co", whatsapp_number="12345")


def test_update_my_profile_rejects_a_too_long_whatsapp_number(make_supplier):
    supplier = make_supplier()

    with pytest.raises(ProfileValidationError):
        supplier_profile_service.update_my_profile(
            supplier.id, business_name="Co", whatsapp_number="1234567890123456789"
        )


def test_update_my_profile_strips_a_leading_at_from_tiktok_handle(make_supplier):
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(
        supplier.id, business_name="Co", tiktok_handle="@my.shop_123"
    )

    assert profile.tiktok_handle == "my.shop_123"


def test_update_my_profile_rejects_a_tiktok_handle_with_invalid_characters(make_supplier):
    """A pasted full URL or an @-mention with spaces should be caught,
    not silently stored as garbage."""
    supplier = make_supplier()

    with pytest.raises(ProfileValidationError):
        supplier_profile_service.update_my_profile(
            supplier.id, business_name="Co", tiktok_handle="https://tiktok.com/@myshop"
        )


def test_update_my_profile_accepts_a_valid_contact_email(make_supplier):
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(
        supplier.id, business_name="Co", contact_email="orders@myshop.co.za"
    )

    assert profile.contact_email == "orders@myshop.co.za"


def test_update_my_profile_persists_share_contact_details_toggle(make_supplier):
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(
        supplier.id, business_name="Co", whatsapp_number="27821234567", share_contact_details=True
    )

    assert profile.share_contact_details is True


def test_update_my_profile_defaults_share_contact_details_to_false(make_supplier):
    """Cautious default -- nothing shows until explicitly opted in,
    same philosophy as VisibleImageSource.NONE's own default."""
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(supplier.id, business_name="Co")

    assert profile.share_contact_details is False


def test_update_my_profile_all_contact_fields_are_genuinely_optional(make_supplier):
    """A supplier who doesn't want to share anything can save a
    perfectly valid profile with all three contact fields blank."""
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(supplier.id, business_name="Co")

    assert profile.whatsapp_number is None
    assert profile.contact_email is None
    assert profile.tiktok_handle is None


# --- photo_visibility / visible_image_source, now genuinely writable ---


def test_update_my_profile_persists_photo_visibility(make_supplier):
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(
        supplier.id, business_name="Co", photo_visibility="everyone"
    )

    assert profile.photo_visibility == PhotoVisibility.EVERYONE


def test_update_my_profile_rejects_an_invalid_photo_visibility_value(make_supplier):
    supplier = make_supplier()

    with pytest.raises(ProfileValidationError):
        supplier_profile_service.update_my_profile(supplier.id, business_name="Co", photo_visibility="not_a_real_value")


def test_update_my_profile_persists_visible_image_source(make_supplier):
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(
        supplier.id, business_name="Co", visible_image_source="business"
    )

    assert profile.visible_image_source == VisibleImageSource.BUSINESS


def test_update_my_profile_can_be_called_repeatedly_on_the_same_profile(make_supplier):
    """The real proof this is genuinely persisted, not mock-faked --
    two separate calls, second one's changes actually stick."""
    supplier = make_supplier()

    supplier_profile_service.update_my_profile(supplier.id, business_name="First Name")
    profile = supplier_profile_service.update_my_profile(supplier.id, business_name="Second Name")

    refetched = supplier_profile_service.get_my_profile(supplier.id)
    assert refetched.business_name == "Second Name"
    assert profile.business_name == "Second Name"
