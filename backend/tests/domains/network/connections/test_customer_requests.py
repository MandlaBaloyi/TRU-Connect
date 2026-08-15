"""
Customer Requests (Supplier Approval) tests -- file.txt Phase 3 /
FILE2.txt's own "PHASE 3 -- SUPPLIER APPROVAL". The other half of
test_connection_requests.py: a business creates a PENDING request via
request_connection(); these tests confirm the SUPPLIER's side of that
same row -- listing, viewing, approving, declining.
"""
from __future__ import annotations

from src.domains.network.connections.services import connections_service
from src.domains.network.connections.services.errors import ConnectionRequestNotFoundError
import pytest


def _pending_request(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Test Wholesale")
    connections_service.request_connection(business.id, profile.id)
    return business, supplier_user, profile


def test_customer_requests_list_starts_empty(make_supplier):
    supplier_user = make_supplier()
    results = connections_service.get_customer_requests(supplier_user.id)
    assert results == []


def test_pending_request_appears_in_customer_requests_list(make_business, make_supplier, make_supplier_profile):
    business, supplier_user, profile = _pending_request(make_business, make_supplier, make_supplier_profile)

    results = connections_service.get_customer_requests(supplier_user.id)
    assert len(results) == 1
    assert results[0]["status"] == "PENDING"


def test_approve_sets_status_active(make_business, make_supplier, make_supplier_profile):
    business, supplier_user, profile = _pending_request(make_business, make_supplier, make_supplier_profile)
    request_id = connections_service.get_customer_requests(supplier_user.id)[0]["id"]

    result = connections_service.approve_request(supplier_user.id, request_id)
    assert result["status"] == "ACTIVE"


def test_approved_request_drops_off_pending_list(make_business, make_supplier, make_supplier_profile):
    business, supplier_user, profile = _pending_request(make_business, make_supplier, make_supplier_profile)
    request_id = connections_service.get_customer_requests(supplier_user.id)[0]["id"]

    connections_service.approve_request(supplier_user.id, request_id)
    results = connections_service.get_customer_requests(supplier_user.id)
    assert results == []


def test_decline_sets_status_declined(make_business, make_supplier, make_supplier_profile):
    business, supplier_user, profile = _pending_request(make_business, make_supplier, make_supplier_profile)
    request_id = connections_service.get_customer_requests(supplier_user.id)[0]["id"]

    result = connections_service.decline_request(supplier_user.id, request_id)
    assert result["status"] == "DECLINED"


def test_approving_twice_is_idempotent(make_business, make_supplier, make_supplier_profile):
    business, supplier_user, profile = _pending_request(make_business, make_supplier, make_supplier_profile)
    request_id = connections_service.get_customer_requests(supplier_user.id)[0]["id"]

    connections_service.approve_request(supplier_user.id, request_id)
    result = connections_service.approve_request(supplier_user.id, request_id)
    assert result["status"] == "ACTIVE"


def test_approving_after_business_requested_updates_their_view_too(
    make_business, make_supplier, make_supplier_profile
):
    """Confirms approve_request and get_supplier_profile (the
    business's OWN view, built for Find Supplier) read the exact same
    underlying row -- approval on the supplier side must be visible
    from the business side without any extra wiring."""
    business, supplier_user, profile = _pending_request(make_business, make_supplier, make_supplier_profile)
    request_id = connections_service.get_customer_requests(supplier_user.id)[0]["id"]

    connections_service.approve_request(supplier_user.id, request_id)

    preview = connections_service.get_supplier_profile(business.id, profile.id)
    assert preview["connectionStatus"] == "ACTIVE"


def test_nonexistent_request_raises_not_found(make_supplier):
    import uuid

    supplier_user = make_supplier()
    with pytest.raises(ConnectionRequestNotFoundError):
        connections_service.get_customer_request_detail(supplier_user.id, uuid.uuid4())
