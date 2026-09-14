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


# --- collection address (supplier's own premises, Mapbox pin-drop) ---------


def test_update_my_profile_persists_collection_address(make_supplier):
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(
        supplier.id,
        business_name="Fresh Foods Wholesale",
        collection_building="Warehouse 3",
        collection_street="Market Street",
        collection_suburb="Seshego",
        collection_city="Polokwane",
        collection_province="Limpopo",
        collection_postal_code="0742",
        collection_latitude=-23.8500,
        collection_longitude=29.4000,
    )

    assert profile.collection_building == "Warehouse 3"
    assert profile.collection_street == "Market Street"
    assert profile.collection_suburb == "Seshego"
    assert profile.collection_city == "Polokwane"
    assert profile.collection_province == "Limpopo"
    assert profile.collection_postal_code == "0742"
    assert float(profile.collection_latitude) == pytest.approx(-23.8500)
    assert float(profile.collection_longitude) == pytest.approx(29.4000)


def test_update_my_profile_collection_address_is_genuinely_optional(make_supplier):
    """A supplier who hasn't set up a collection address yet still has
    a fully working profile otherwise -- same "optional, not required"
    reasoning as every contact field above."""
    supplier = make_supplier()

    profile = supplier_profile_service.update_my_profile(supplier.id, business_name="No Address Yet Co")

    assert profile.collection_street is None
    assert profile.collection_latitude is None


def test_update_my_profile_rejects_out_of_range_collection_coordinates(make_supplier):
    supplier = make_supplier()

    with pytest.raises(ProfileValidationError):
        supplier_profile_service.update_my_profile(
            supplier.id, business_name="Bad Coords Co", collection_latitude=999.0, collection_longitude=29.0
        )


class TestHowThisSupplierWantsToBePaid:
    """The two flags existed and were ENFORCED at checkout since the
    d0e1f2345678 migration -- a business simply could not pay by a
    method the supplier had not enabled. What did not exist was any way
    for a supplier to set them, or for anyone to read them: they were in
    no schema, no service and no response, so every supplier was stuck
    on the column defaults (direct on, digital off) forever."""

    def test_a_supplier_can_turn_the_digital_rail_on(self, make_supplier):
        supplier = make_supplier()

        profile = supplier_profile_service.update_my_profile(
            supplier.id,
            business_name="Digital Wholesale",
            accepts_direct_payment=False,
            accepts_digital_payment=True,
        )

        assert profile.accepts_digital_payment is True
        assert profile.accepts_direct_payment is False

    def test_accepting_neither_is_refused(self, make_supplier):
        """THE TRAP THIS CLOSES. checkout_service checks every method
        against these flags, so a supplier with both off is not a
        cash-only supplier -- they are a shopfront that looks open and
        rejects every order at the final step, with an error message
        that blames the buyer's choice of payment method."""
        supplier = make_supplier()

        with pytest.raises(ProfileValidationError) as exc:
            supplier_profile_service.update_my_profile(
                supplier.id,
                business_name="Unpayable Wholesale",
                accepts_direct_payment=False,
                accepts_digital_payment=False,
            )

        # AppError carries the field messages on .errors, not in args.
        assert any("at least one" in str(m).lower() for m in exc.value.errors)

    def test_a_supplier_who_never_opens_the_screen_keeps_their_rail(self, make_supplier):
        """The update schema is a FULL REPLACE, so an omitted field is
        reset to its load_default. Those defaults match the column
        defaults on purpose -- otherwise a supplier editing their
        business name would silently lose the rail they were trading
        on."""
        from src.domains.supplier.supplier_profile.schemas.supplier_profile_schemas import (
            UpdateSupplierProfileSchema,
        )

        data = UpdateSupplierProfileSchema().load({"business_name": "Unchanged Wholesale"})

        assert data["accepts_direct_payment"] is True
        assert data["accepts_digital_payment"] is False
