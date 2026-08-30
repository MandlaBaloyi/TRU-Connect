"""
Tests for get_my_connections (Community tab's "My Connections") --
ACTIVE only, works symmetrically for both roles.
"""
from __future__ import annotations

from src.domains.network.connections.models.connection_request import ConnectionRequest, ConnectionRequestStatus
from src.domains.network.connections.services import connections_service
from src.extensions import db


def _make_active_connection(business, supplier_profile):
    connections_service.request_connection(business.id, supplier_profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=supplier_profile.id).first()
    request.status = ConnectionRequestStatus.ACTIVE
    db.session.commit()
    return request


def test_business_sees_its_active_connections(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Active Supplier Co")
    _make_active_connection(business, profile)

    results = connections_service.get_my_connections(business.id, "business")

    assert len(results) == 1
    assert results[0]["name"] == "Active Supplier Co"
    assert results[0]["connectedSince"] is not None


def test_supplier_sees_its_active_connections(make_business, make_business_profile, make_supplier):
    business = make_business()
    business_profile = make_business_profile(business, business_name="Active Business Co")
    supplier_user = make_supplier()

    connections_service.request_connection_to_business(supplier_user.id, business_profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id).first()
    request.status = ConnectionRequestStatus.ACTIVE
    db.session.commit()

    results = connections_service.get_my_connections(supplier_user.id, "supplier")

    assert len(results) == 1
    assert results[0]["name"] == "Active Business Co"


def test_business_viewer_gets_the_suppliers_own_profile_id(make_business, make_supplier, make_supplier_profile):
    """THE REAL GAP THIS FIXES -- other_party_id must be the supplier's
    own supplier_profile_id (what the frontend route actually needs to
    tap through to their products), not the connection request's own
    id."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Active Supplier Co")
    _make_active_connection(business, profile)

    results = connections_service.get_my_connections(business.id, "business")

    assert results[0]["other_party_id"] == str(profile.id)
    assert results[0]["other_party_id"] != results[0]["id"]  # never the connection request's own id


def test_supplier_viewer_gets_the_businesss_own_profile_id_not_the_raw_user_id(
    make_business, make_business_profile, make_supplier
):
    """THE SUBTLER HALF OF THE SAME FIX -- BusinessProfile.id is a
    genuinely different value from the raw auth.users.id
    ConnectionRequest.business_id stores; other_party_id must be the
    PROFILE id, matching what GET /businesses/<id> actually expects."""
    business = make_business()
    business_profile = make_business_profile(business, business_name="Active Business Co")
    supplier_user = make_supplier()

    connections_service.request_connection_to_business(supplier_user.id, business_profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id).first()
    request.status = ConnectionRequestStatus.ACTIVE
    db.session.commit()

    results = connections_service.get_my_connections(supplier_user.id, "supplier")

    assert results[0]["other_party_id"] == str(business_profile.id)
    assert results[0]["other_party_id"] != str(business.id)  # never the raw user id


def test_pending_connections_do_not_appear(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Still Pending Co")
    connections_service.request_connection(business.id, profile.id)  # stays PENDING, never approved

    results = connections_service.get_my_connections(business.id, "business")

    assert results == []


def test_declined_connections_do_not_appear(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Declined Co")
    connections_service.request_connection(business.id, profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    request.status = ConnectionRequestStatus.DECLINED
    db.session.commit()

    results = connections_service.get_my_connections(business.id, "business")

    assert results == []


def test_different_businesses_never_see_each_others_connections(
    make_business, make_supplier, make_supplier_profile
):
    business_a = make_business("connections-a@example.com")
    business_b = make_business("connections-b@example.com")
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Shared Target Co")
    _make_active_connection(business_a, profile)

    assert len(connections_service.get_my_connections(business_a.id, "business")) == 1
    assert connections_service.get_my_connections(business_b.id, "business") == []


def test_connection_initiated_by_either_side_appears_once_active(
    make_business, make_business_profile, make_supplier, make_supplier_profile
):
    """The list doesn't care who initiated -- only that it's ACTIVE."""
    business = make_business()
    business_profile = make_business_profile(business, business_name="Either Direction Co")
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Either Direction Supplier")

    # Supplier-initiated this time, not business-initiated.
    connections_service.request_connection_to_business(supplier_user.id, business_profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    request.status = ConnectionRequestStatus.ACTIVE
    db.session.commit()

    business_side = connections_service.get_my_connections(business.id, "business")
    supplier_side = connections_service.get_my_connections(supplier_user.id, "supplier")

    assert len(business_side) == 1
    assert len(supplier_side) == 1
