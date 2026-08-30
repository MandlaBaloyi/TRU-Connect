"""
HTTP-level tests for supplier_profile_routes.py -- the first real
routes this domain has ever had.
"""
from __future__ import annotations

from flask_jwt_extended import create_access_token


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def _auth(user, role: str) -> dict:
    return {"Authorization": f"Bearer {_token_for(user, role)}"}


def test_get_my_profile_via_http_creates_one_if_none_exists(client, make_supplier):
    supplier = make_supplier()

    response = client.get("/api/v1/supplier-discovery/my-profile", headers=_auth(supplier, "supplier"))

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["shareContactDetails"] is False
    assert data["whatsappNumber"] is None


def test_update_my_profile_via_http_persists_real_changes(client, make_supplier):
    supplier = make_supplier()

    response = client.patch(
        "/api/v1/supplier-discovery/my-profile",
        json={
            "business_name": "Real Wholesale Co",
            "whatsapp_number": "+27 82 123 4567",
            "contact_email": "orders@myshop.co.za",
            "tiktok_handle": "@myshop",
            "share_contact_details": True,
        },
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["businessName"] == "Real Wholesale Co"
    assert data["whatsappNumber"] == "27821234567"
    assert data["contactEmail"] == "orders@myshop.co.za"
    assert data["tiktokHandle"] == "myshop"
    assert data["shareContactDetails"] is True

    # Confirmed genuinely persisted, not just echoed back -- a fresh
    # GET reflects the same real change.
    refetched = client.get("/api/v1/supplier-discovery/my-profile", headers=_auth(supplier, "supplier"))
    assert refetched.get_json()["data"]["businessName"] == "Real Wholesale Co"


def test_update_my_profile_via_http_rejects_blank_business_name(client, make_supplier):
    supplier = make_supplier()

    response = client.patch(
        "/api/v1/supplier-discovery/my-profile",
        json={"business_name": "   "},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_update_my_profile_via_http_rejects_an_invalid_email_format(client, make_supplier):
    supplier = make_supplier()

    response = client.patch(
        "/api/v1/supplier-discovery/my-profile",
        json={"business_name": "Co", "contact_email": "not-an-email"},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_update_my_profile_via_http_rejects_an_invalid_whatsapp_number(client, make_supplier):
    supplier = make_supplier()

    response = client.patch(
        "/api/v1/supplier-discovery/my-profile",
        json={"business_name": "Co", "whatsapp_number": "123"},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_my_profile_routes_reject_a_business_role(client, make_business):
    business = make_business()

    get_response = client.get("/api/v1/supplier-discovery/my-profile", headers=_auth(business, "business"))
    patch_response = client.patch(
        "/api/v1/supplier-discovery/my-profile", json={"business_name": "Co"}, headers=_auth(business, "business")
    )

    assert get_response.status_code == 403
    assert patch_response.status_code == 403
