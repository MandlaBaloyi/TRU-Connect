"""
Supplier Discovery HTTP-layer tests -- real requests through the real
Flask test client, matching test_auth.py's own approach (drive
everything through `client`, not the service layer directly).

role_required("business") is the one genuinely new piece of
authorization in this domain (see api/connections_routes.py's
own docstring on why: it's unused everywhere else in this codebase).
test_supplier_role_is_rejected is the test that actually proves it
does something, not just that it's present in the decorator stack.
"""
from __future__ import annotations

from flask_jwt_extended import create_access_token


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def test_business_can_search(client, make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    make_supplier_profile(supplier_user, business_name="HTTP Test Wholesale")

    response = client.get(
        "/api/v1/supplier-discovery/search?q=HTTP",
        headers={"Authorization": f"Bearer {_token_for(business, 'business')}"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["results"][0]["businessName"] == "HTTP Test Wholesale"


def test_supplier_role_is_rejected(client, make_business, make_supplier, make_supplier_profile):
    """A valid, fully-authenticated SUPPLIER account must still be
    blocked from a business-only endpoint -- role_required is what's
    being tested here, not authentication itself."""
    supplier_user = make_supplier()
    make_supplier_profile(supplier_user, business_name="HTTP Test Wholesale")

    response = client.get(
        "/api/v1/supplier-discovery/search?q=HTTP",
        headers={"Authorization": f"Bearer {_token_for(supplier_user, 'supplier')}"},
    )

    assert response.status_code == 403


def test_unauthenticated_request_is_rejected(client):
    response = client.get("/api/v1/supplier-discovery/search?q=HTTP")
    assert response.status_code == 401


def test_connection_request_round_trip(client, make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="HTTP Test Wholesale")

    response = client.post(
        f"/api/v1/supplier-discovery/suppliers/{profile.id}/connection-requests",
        headers={"Authorization": f"Bearer {_token_for(business, 'business')}"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["connectionStatus"] == "PENDING"


def test_short_query_returns_validation_error_envelope(client, make_business):
    business = make_business()

    response = client.get(
        "/api/v1/supplier-discovery/search?q=A",
        headers={"Authorization": f"Bearer {_token_for(business, 'business')}"},
    )

    assert response.status_code == 422
    body = response.get_json()
    assert body["success"] is False
    assert body["code"] == "INVALID_SEARCH_QUERY"


def test_nonexistent_supplier_returns_404(client, make_business):
    import uuid

    business = make_business()

    response = client.get(
        f"/api/v1/supplier-discovery/suppliers/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {_token_for(business, 'business')}"},
    )

    assert response.status_code == 404
    assert response.get_json()["code"] == "SUPPLIER_NOT_FOUND"
