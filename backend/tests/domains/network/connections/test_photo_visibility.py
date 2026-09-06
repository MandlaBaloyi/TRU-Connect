"""
Tests for photo visibility (photo_visibility / visible_image_source),
agreed during architecture review: a profile photo now reaches the
OTHER party in a connection, gated by two independent settings. Real
Postgres, both roles, covering the meaningful combinations rather than
every permutation.
"""
from __future__ import annotations

from src.domains.network.connections.models.connection_request import ConnectionRequest, ConnectionRequestStatus
from src.domains.network.connections.services import (
    discovery_service,
    request_service,
)
from src.extensions import db


def _make_active_connection(business, supplier_profile):
    request_service.request_connection(business.id, supplier_profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=supplier_profile.id).first()
    request.status = ConnectionRequestStatus.ACTIVE
    db.session.commit()


def _set_supplier_photo(supplier_user, profile, *, visible_image_source=None, photo_visibility=None):
    from src.domains.supplier.supplier_profile.models.supplier_profile import PhotoVisibility, VisibleImageSource

    if visible_image_source is not None:
        profile.visible_image_source = VisibleImageSource(visible_image_source)
    if photo_visibility is not None:
        profile.photo_visibility = PhotoVisibility(photo_visibility)
    db.session.commit()


def test_new_profile_defaults_to_no_photo_shown(make_business, make_supplier, make_supplier_profile):
    """Brand new profile, nothing configured -- both defaults
    (visible_image_source=NONE, photo_visibility=CONNECTIONS) should
    combine to show nothing, even with an active connection."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Default State Co")
    _make_active_connection(business, profile)

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["photoUrl"] is None


def test_nobody_visibility_hides_photo_even_when_connected(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    profile = make_supplier_profile(supplier_user, business_name="Nobody Sees Co")
    _set_supplier_photo(supplier_user, profile, visible_image_source="personal", photo_visibility="nobody")
    _make_active_connection(business, profile)
    db.session.commit()

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["photoUrl"] is None


def test_connections_visibility_hides_photo_when_not_active(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    profile = make_supplier_profile(supplier_user, business_name="Not Connected Yet Co")
    _set_supplier_photo(supplier_user, profile, visible_image_source="personal", photo_visibility="connections")
    db.session.commit()
    # No connection made at all -- NOT_REQUESTED.

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["photoUrl"] is None


def test_connections_visibility_shows_photo_once_active(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    profile = make_supplier_profile(supplier_user, business_name="Now Connected Co")
    _set_supplier_photo(supplier_user, profile, visible_image_source="personal", photo_visibility="connections")
    db.session.commit()
    _make_active_connection(business, profile)

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["photoUrl"] == "https://example.com/personal.jpg"


def test_everyone_visibility_shows_photo_without_any_connection(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    profile = make_supplier_profile(supplier_user, business_name="Public Co")
    _set_supplier_photo(supplier_user, profile, visible_image_source="personal", photo_visibility="everyone")
    db.session.commit()
    # No connection at all.

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["photoUrl"] == "https://example.com/personal.jpg"


def test_none_source_hides_photo_even_under_everyone_visibility(make_business, make_supplier, make_supplier_profile):
    """The source gate is independent of the visibility gate -- even
    the widest visibility setting shows nothing until a source is
    actively chosen."""
    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    profile = make_supplier_profile(supplier_user, business_name="Nothing Chosen Co")
    _set_supplier_photo(supplier_user, profile, photo_visibility="everyone")  # source stays default NONE
    db.session.commit()

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["photoUrl"] is None


def test_business_source_resolves_to_business_image_not_personal(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    supplier_user.profile_image_url = "https://example.com/personal.jpg"
    profile = make_supplier_profile(supplier_user, business_name="Shows Business Image Co")
    profile.business_image_url = "https://example.com/business-logo.jpg"
    _set_supplier_photo(supplier_user, profile, visible_image_source="business", photo_visibility="everyone")
    db.session.commit()

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["photoUrl"] == "https://example.com/business-logo.jpg"


def test_business_side_photo_resolution_mirrors_supplier_side(
    make_business, make_business_profile, make_supplier
):
    """Same resolution rule, other direction -- a business's photo
    shown to a connected supplier."""
    business = make_business()
    business.profile_image_url = "https://example.com/business-owner.jpg"
    business_profile = make_business_profile(business, business_name="Mirror Test Biz")

    from src.domains.business.business_profile.models.business_profile import PhotoVisibility, VisibleImageSource

    business_profile.visible_image_source = VisibleImageSource.PERSONAL
    business_profile.photo_visibility = PhotoVisibility.CONNECTIONS
    db.session.commit()

    supplier_user = make_supplier()
    request_service.request_connection_to_business(supplier_user.id, business_profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id).first()
    request.status = ConnectionRequestStatus.ACTIVE
    db.session.commit()

    result = discovery_service.get_business_profile(supplier_user.id, business_profile.id)

    assert result["photoUrl"] == "https://example.com/business-owner.jpg"


def test_update_my_photo_settings_only_changes_provided_fields(make_supplier, make_supplier_profile):
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Partial Update Co")
    _set_supplier_photo(supplier_user, profile, visible_image_source="personal", photo_visibility="everyone")

    # Only update photo_visibility -- visible_image_source must stay "personal".
    result = discovery_service.update_my_photo_settings(supplier_user.id, "supplier", photo_visibility="nobody")

    assert result["photoVisibility"] == "nobody"
    assert result["visibleImageSource"] == "personal"


def test_update_my_photo_settings_works_for_business_role(make_business, make_business_profile):
    business = make_business()
    make_business_profile(business, business_name="Settings Update Biz")

    result = discovery_service.update_my_photo_settings(
        business.id, "business", visible_image_source="business", photo_visibility="everyone"
    )

    assert result["visibleImageSource"] == "business"
    assert result["photoVisibility"] == "everyone"
