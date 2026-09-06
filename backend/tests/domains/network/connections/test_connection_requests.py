"""
Connection request tests -- file.txt Phase 2's minimal Phase-1 slice:
a business can request a connection, and requesting twice never
creates two rows or errors (matches the frontend mock's own documented
idempotent behaviour exactly -- see services/connections_service.py's
docstring on request_connection).
"""
from __future__ import annotations

from src.domains.network.connections.models.connection_request import ConnectionRequest
from src.domains.network.connections.services import (
    discovery_service,
    request_service,
)


def _profile(make_supplier, make_supplier_profile):
    supplier_user = make_supplier("supplier@example.com")
    return make_supplier_profile(supplier_user, business_name="Test Wholesale")


def test_profile_preview_starts_not_requested(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    profile = _profile(make_supplier, make_supplier_profile)

    preview = discovery_service.get_supplier_profile(business.id, profile.id)
    assert preview["connectionStatus"] == "NOT_REQUESTED"


def test_request_connection_returns_pending(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    profile = _profile(make_supplier, make_supplier_profile)

    result = request_service.request_connection(business.id, profile.id)
    assert result["connectionStatus"] == "PENDING"


def test_profile_preview_reflects_pending_after_request(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    profile = _profile(make_supplier, make_supplier_profile)

    request_service.request_connection(business.id, profile.id)
    preview = discovery_service.get_supplier_profile(business.id, profile.id)
    assert preview["connectionStatus"] == "PENDING"


def test_double_request_is_idempotent_exactly_one_row(
    make_business, make_supplier, make_supplier_profile, db_session
):
    """Double-tap / retried request must never create a second row --
    this is the actual guarantee behind the DB's own
    uq_connection_requests_business_supplier constraint, exercised at
    the service layer where a normal caller would hit it."""
    business = make_business()
    profile = _profile(make_supplier, make_supplier_profile)

    request_service.request_connection(business.id, profile.id)
    request_service.request_connection(business.id, profile.id)

    count = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).count()
    assert count == 1
