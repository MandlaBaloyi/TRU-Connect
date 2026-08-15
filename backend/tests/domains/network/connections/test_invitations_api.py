"""
Supplier Invitation HTTP-layer tests -- real requests through the real
Flask test client, matching test_api.py's own approach.
"""
from __future__ import annotations

from flask_jwt_extended import create_access_token


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def test_business_can_invite_supplier(client, make_business):
    business = make_business()
    response = client.post(
        "/api/v1/supplier-discovery/invitations",
        json={"email": "invited@example.com"},
        headers={"Authorization": f"Bearer {_token_for(business, 'business')}"},
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "SENT"


def test_supplier_cannot_invite_supplier(client, make_supplier):
    """invite_supplier is business-only -- the mirror of every other
    business-only route in this domain."""
    supplier_user = make_supplier()
    response = client.post(
        "/api/v1/supplier-discovery/invitations",
        json={"email": "invited2@example.com"},
        headers={"Authorization": f"Bearer {_token_for(supplier_user, 'supplier')}"},
    )
    assert response.status_code == 403


def test_invalid_email_returns_validation_error(client, make_business):
    business = make_business()
    response = client.post(
        "/api/v1/supplier-discovery/invitations",
        json={"email": "not-an-email"},
        headers={"Authorization": f"Bearer {_token_for(business, 'business')}"},
    )
    assert response.status_code == 422


def test_validate_invitation_endpoint_requires_no_auth(client):
    """Deliberately unauthenticated -- someone without an account yet
    must be able to check their invite link. Confirms this by NOT
    sending an Authorization header at all."""
    response = client.get("/api/v1/supplier-discovery/invitations/validate?ticket=whatever")
    assert response.status_code == 200
    assert response.get_json()["data"]["valid"] is False


def test_validate_invitation_endpoint_true_for_real_ticket(client, make_business):
    import re

    from src.shared.email.email import get_fake_provider

    business = make_business()
    get_fake_provider().clear()
    client.post(
        "/api/v1/supplier-discovery/invitations",
        json={"email": "realticket@example.com"},
        headers={"Authorization": f"Bearer {_token_for(business, 'business')}"},
    )
    sent = [e for e in get_fake_provider().sent_emails if e["to"] == "realticket@example.com"][0]
    ticket = re.search(r"ticket=([\w-]+)", sent["html_body"]).group(1)

    response = client.get(f"/api/v1/supplier-discovery/invitations/validate?ticket={ticket}")
    assert response.status_code == 200
    assert response.get_json()["data"]["valid"] is True
