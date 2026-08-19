"""
Find Business + Supplier Requests tests -- the reverse direction of
Find Supplier / Customer Requests. Same IDOR-safety discipline as
test_ownership.py and test_customer_requests_ownership.py, mirrored
for the other side of the relationship.

Also carries the reverse-direction half of the name/business-name-only
search redesign's regression coverage (see test_search.py's own module
docstring for the full reasoning) -- test_searching_by_a_real_
registered_phone_or_email_no_longer_matches and
test_search_result_shape_has_no_matched_field_or_identifier below.
"""
from __future__ import annotations

import pytest

from src.domains.network.connections.services import connections_service
from src.domains.network.connections.services.errors import ConnectionRequestNotFoundError


def test_supplier_can_find_business_by_name(make_supplier, make_business, make_business_profile):
    supplier_user = make_supplier()
    business = make_business()
    make_business_profile(business, business_name="Findable Traders")

    results = connections_service.search_businesses("Findable", supplier_user.id)
    assert len(results) == 1
    assert results[0]["businessName"] == "Findable Traders"


def test_search_result_shape_has_no_matched_field_or_identifier(make_supplier, make_business, make_business_profile):
    """Mirrors test_search.py's own equivalent test -- Find Business's
    to_search_result_dict was simplified identically to Find Supplier's,
    see BusinessProfile.to_search_result_dict's own docstring."""
    supplier_user = make_supplier()
    business = make_business()
    make_business_profile(business, business_name="Shape Check Traders")

    results = connections_service.search_businesses("Shape Check", supplier_user.id)
    assert "matchedField" not in results[0]
    assert "maskedMatchedIdentifier" not in results[0]
    assert set(results[0].keys()) == {"id", "businessName", "category", "location", "photoUrl"}


def test_searching_by_a_real_registered_phone_or_email_no_longer_matches(
    make_supplier, make_business, make_business_profile
):
    """Reverse-direction mirror of test_search.py's own core regression
    test -- a business with a real, stored normalized_phone/
    normalized_email must no longer be findable by either, proving the
    enumeration-vector fix applies on this side too, not just Find
    Supplier's."""
    from src.shared.validation.identifiers import normalize_email, normalize_phone

    supplier_user = make_supplier()
    business = make_business()
    make_business_profile(
        business,
        business_name="Reverse Regression Traders",
        normalized_phone=normalize_phone("082 987 6543"),
        normalized_email=normalize_email("Owner@ReverseRegression.co.za"),
    )

    assert connections_service.search_businesses("082 987 6543", supplier_user.id) == []
    assert connections_service.search_businesses("owner@reverseregression.co.za", supplier_user.id) == []


def test_supplier_requests_connection_to_business(make_supplier, make_business, make_business_profile):
    supplier_user = make_supplier()
    business = make_business()
    business_profile = make_business_profile(business, business_name="Connect Target")

    result = connections_service.request_connection_to_business(supplier_user.id, business_profile.id)
    assert result["connectionStatus"] == "PENDING"


def test_supplier_initiated_request_appears_in_supplier_requests(
    make_supplier, make_business, make_business_profile
):
    supplier_user = make_supplier()
    business = make_business()
    business_profile = make_business_profile(business, business_name="Appears Here Co")

    connections_service.request_connection_to_business(supplier_user.id, business_profile.id)

    results = connections_service.get_supplier_requests(business.id)
    assert len(results) == 1
    assert results[0]["status"] == "PENDING"


def test_supplier_initiated_request_does_not_appear_in_customer_requests(
    make_supplier, make_business, make_business_profile
):
    """A supplier who INITIATED a request to a business must not see
    it in their OWN Customer Requests -- that list is for requests
    THEY need to approve, and they created this one themselves."""
    supplier_user = make_supplier()
    business = make_business()
    business_profile = make_business_profile(business, business_name="No Leak Co")

    connections_service.request_connection_to_business(supplier_user.id, business_profile.id)

    assert connections_service.get_customer_requests(supplier_user.id) == []


def test_business_initiated_request_does_not_appear_in_supplier_requests(
    make_business, make_supplier, make_supplier_profile
):
    """The mirror check, other direction: a business's own
    Find-Supplier-initiated request must not appear in ITS OWN
    Supplier Requests (the list for requests it needs to approve)."""
    business = make_business()
    supplier_user = make_supplier()
    supplier_profile = make_supplier_profile(supplier_user, business_name="No Leak Supplier")

    connections_service.request_connection(business.id, supplier_profile.id)

    assert connections_service.get_supplier_requests(business.id) == []


def test_different_business_cannot_view_supplier_requests_of_another(
    make_supplier, make_business, make_business_profile
):
    supplier_user = make_supplier()
    business_a = make_business("business-a@example.com")
    business_b = make_business("business-b@example.com")
    profile_a = make_business_profile(business_a, business_name="Business A Target")

    connections_service.request_connection_to_business(supplier_user.id, profile_a.id)
    request_id = connections_service.get_supplier_requests(business_a.id)[0]["id"]

    with pytest.raises(ConnectionRequestNotFoundError):
        connections_service.get_supplier_request_detail(business_b.id, request_id)


def test_different_business_cannot_approve_supplier_request_of_another(
    make_supplier, make_business, make_business_profile
):
    supplier_user = make_supplier()
    business_a = make_business("approve-a@example.com")
    business_b = make_business("approve-b@example.com")
    profile_a = make_business_profile(business_a, business_name="Approve Target")

    connections_service.request_connection_to_business(supplier_user.id, profile_a.id)
    request_id = connections_service.get_supplier_requests(business_a.id)[0]["id"]

    with pytest.raises(ConnectionRequestNotFoundError):
        connections_service.approve_supplier_request(business_b.id, request_id)

    results = connections_service.get_supplier_requests(business_a.id)
    assert results[0]["status"] == "PENDING"


def test_business_approves_supplier_initiated_request(make_supplier, make_business, make_business_profile):
    supplier_user = make_supplier()
    business = make_business()
    business_profile = make_business_profile(business, business_name="Approve Me Co")

    connections_service.request_connection_to_business(supplier_user.id, business_profile.id)
    request_id = connections_service.get_supplier_requests(business.id)[0]["id"]

    result = connections_service.approve_supplier_request(business.id, request_id)
    assert result["status"] == "ACTIVE"

    # Request drops off the pending list once approved.
    assert connections_service.get_supplier_requests(business.id) == []
