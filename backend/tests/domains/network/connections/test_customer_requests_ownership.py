"""
Ownership / IDOR tests, supplier side -- same convention as
test_ownership.py (the business side) and loan_book's own
test_ownership.py. Supplier A has a real pending request against them.
Supplier B -- a completely separate, real supplier -- must not be able
to see or act on it using its real id.
"""
from __future__ import annotations

import pytest

from src.domains.network.connections.services import (
    request_service,
)
from src.domains.network.connections.services.errors import ConnectionRequestNotFoundError


def test_supplier_b_cannot_view_supplier_as_request(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_a = make_supplier("supplier-a@example.com")
    supplier_b = make_supplier("supplier-b@example.com")
    profile_a = make_supplier_profile(supplier_a, business_name="Supplier A's Business")

    request_service.request_connection(business.id, profile_a.id)
    request_id = request_service.get_customer_requests(supplier_a.id)[0]["id"]

    with pytest.raises(ConnectionRequestNotFoundError):
        request_service.get_customer_request_detail(supplier_b.id, request_id)


def test_supplier_b_cannot_approve_supplier_as_request(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_a = make_supplier("approve-a@example.com")
    supplier_b = make_supplier("approve-b@example.com")
    profile_a = make_supplier_profile(supplier_a, business_name="Approve Target")

    request_service.request_connection(business.id, profile_a.id)
    request_id = request_service.get_customer_requests(supplier_a.id)[0]["id"]

    with pytest.raises(ConnectionRequestNotFoundError):
        request_service.approve_request(supplier_b.id, request_id)

    # Confirm it's STILL pending from A's own point of view -- B's
    # failed attempt must not have changed anything.
    results = request_service.get_customer_requests(supplier_a.id)
    assert len(results) == 1
    assert results[0]["status"] == "PENDING"


def test_supplier_b_requests_list_never_shows_supplier_as_requests(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_a = make_supplier("list-a@example.com")
    supplier_b = make_supplier("list-b@example.com")
    profile_a = make_supplier_profile(supplier_a, business_name="List Target")

    request_service.request_connection(business.id, profile_a.id)

    assert len(request_service.get_customer_requests(supplier_a.id)) == 1
    assert request_service.get_customer_requests(supplier_b.id) == []
