"""
Tests for photo resolution IN SEARCH RESULTS specifically -- revised
per direct product feedback from an earlier design decision that had
deliberately excluded photos from search entirely. Same resolution
rule as profile previews, just proven at the search layer too.
"""
from __future__ import annotations

from src.domains.network.connections.services import connections_service


def _set_supplier_photo(supplier_user, profile, *, visible_image_source=None, photo_visibility=None):
    from src.domains.supplier.supplier_profile.models.supplier_profile import PhotoVisibility, VisibleImageSource
    from src.extensions import db

    if visible_image_source is not None:
        profile.visible_image_source = VisibleImageSource(visible_image_source)
    if photo_visibility is not None:
        profile.photo_visibility = PhotoVisibility(photo_visibility)
    db.session.commit()


def test_everyone_visibility_shows_photo_in_search_results(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    profile = make_supplier_profile(supplier_user, business_name="Search Visible Co")
    _set_supplier_photo(supplier_user, profile, visible_image_source="personal", photo_visibility="everyone")

    results = connections_service.search_suppliers("Search Visible", business.id)

    assert len(results) == 1
    assert results[0]["photoUrl"] == "https://example.com/personal.jpg"


def test_connections_visibility_hides_photo_in_search_before_connecting(
    make_business, make_supplier, make_supplier_profile
):
    """Even though this supplier IS findable, their photo must not
    appear in the result until a real ACTIVE connection exists --
    search returning a result is not the same as being connected."""
    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    profile = make_supplier_profile(supplier_user, business_name="Search Hidden Co")
    _set_supplier_photo(supplier_user, profile, visible_image_source="personal", photo_visibility="connections")

    results = connections_service.search_suppliers("Search Hidden", business.id)

    assert len(results) == 1
    assert results[0]["photoUrl"] is None


def test_default_settings_show_no_photo_in_search(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    make_supplier_profile(supplier_user, business_name="Default Search Co")
    # No photo settings configured -- defaults (NONE source, CONNECTIONS visibility).

    results = connections_service.search_suppliers("Default Search", business.id)

    assert results[0]["photoUrl"] is None


def test_exact_phone_match_also_resolves_photo(make_business, make_supplier, make_supplier_profile):
    """The single-match phone/email branch goes through the same
    to_dict helper as the name-prefix list -- confirmed directly,
    not assumed just because the list branch works."""
    from src.shared.validation.identifiers import normalize_phone

    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    profile = make_supplier_profile(
        supplier_user, business_name="Phone Match Co", normalized_phone=normalize_phone("0712345678")
    )
    _set_supplier_photo(supplier_user, profile, visible_image_source="personal", photo_visibility="everyone")

    results = connections_service.search_suppliers("0712345678", business.id)

    assert len(results) == 1
    assert results[0]["photoUrl"] == "https://example.com/personal.jpg"


def test_reverse_direction_search_also_resolves_photo(make_business, make_business_profile, make_supplier):
    """Same behaviour, Find Business direction."""
    business = make_business()
    business.profile_image_url = "https://example.com/business-owner.jpg"
    business_profile = make_business_profile(business, business_name="Reverse Search Photo Co")

    from src.domains.business.business_profile.models.business_profile import PhotoVisibility, VisibleImageSource
    from src.extensions import db

    business_profile.visible_image_source = VisibleImageSource.PERSONAL
    business_profile.photo_visibility = PhotoVisibility.EVERYONE
    db.session.commit()

    supplier_user = make_supplier()

    results = connections_service.search_businesses("Reverse Search Photo", supplier_user.id)

    assert len(results) == 1
    assert results[0]["photoUrl"] == "https://example.com/business-owner.jpg"
