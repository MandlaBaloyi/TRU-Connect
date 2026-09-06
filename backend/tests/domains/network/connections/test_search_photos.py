"""
Tests for photo resolution IN SEARCH RESULTS specifically -- revised
per direct product feedback from an earlier design decision that had
deliberately excluded photos from search entirely. Same resolution
rule as profile previews, just proven at the search layer too.
"""
from __future__ import annotations

from src.domains.network.connections.services import (
    discovery_service,
)


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

    results = discovery_service.search_suppliers("Search Visible", business.id)

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

    results = discovery_service.search_suppliers("Search Hidden", business.id)

    assert len(results) == 1
    assert results[0]["photoUrl"] is None


def test_default_settings_show_no_photo_in_search(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    make_supplier_profile(supplier_user, business_name="Default Search Co")
    # No photo settings configured -- defaults (NONE source, CONNECTIONS visibility).

    results = discovery_service.search_suppliers("Default Search", business.id)

    assert results[0]["photoUrl"] is None


def test_multiple_name_matches_each_resolve_their_own_photo(make_business, make_supplier, make_supplier_profile):
    """Name-prefix search is the ONLY search path now (phone/email
    exact-match search was removed -- see connections_service.py's own
    _dispatch_search docstring), which means it's also the only path
    that can ever return MORE than one result. This confirms photo
    resolution is genuinely applied per-result in that list, not just
    proven once against a single-item list and assumed to generalize."""
    business = make_business()

    visible_user = make_supplier("visible-photo@example.com")
    visible_user.profile_image_url = "https://example.com/visible.jpg"
    visible_profile = make_supplier_profile(visible_user, business_name="Photo Match Visible Co")
    _set_supplier_photo(visible_user, visible_profile, visible_image_source="personal", photo_visibility="everyone")

    hidden_user = make_supplier("hidden-photo@example.com")
    hidden_user.profile_image_url = "https://example.com/hidden.jpg"
    hidden_profile = make_supplier_profile(hidden_user, business_name="Photo Match Hidden Co")
    _set_supplier_photo(hidden_user, hidden_profile, visible_image_source="personal", photo_visibility="connections")

    results = discovery_service.search_suppliers("Photo Match", business.id)

    by_name = {r["businessName"]: r for r in results}
    assert len(results) == 2
    assert by_name["Photo Match Visible Co"]["photoUrl"] == "https://example.com/visible.jpg"
    assert by_name["Photo Match Hidden Co"]["photoUrl"] is None


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

    results = discovery_service.search_businesses("Reverse Search Photo", supplier_user.id)

    assert len(results) == 1
    assert results[0]["photoUrl"] == "https://example.com/business-owner.jpg"
