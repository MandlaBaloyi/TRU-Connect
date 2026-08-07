"""
HTTP-level ownership tests -- confirms isolation holds through the real
Flask route + JWT auth stack, not just when LoanBookService is called
directly as Python functions (see test_ownership.py for that layer).

Uses the shared app/client fixtures from conftest.py
(create_app("testing")), same as every other test in this project -- no
separate app-building fixture needed here.
"""
from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token

from src.extensions import db


@pytest.fixture()
def two_businesses_with_a_real_entry(app):
    import uuid

    from src.domains.auth.models.user import User, UserRole, VerificationStatus
    from src.domains.business.loan_book.services.loan_book_service import LoanBookService
    from src.shared.finance import Money

    with app.app_context():
        business_a = User(
            id=uuid.uuid4(), email="http-a@example.com", password_hash="x",
            role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED,
        )
        business_b = User(
            id=uuid.uuid4(), email="http-b@example.com", password_hash="x",
            role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED,
        )
        db.session.add_all([business_a, business_b])
        db.session.commit()

        a_customer = LoanBookService.create_customer(business_a.id, "A's customer")
        a_entry = LoanBookService.create_entry(business_a.id, a_customer.id, Money(75000))

        return {
            "token_a": create_access_token(identity=str(business_a.id)),
            "token_b": create_access_token(identity=str(business_b.id)),
            "entry_id": str(a_entry.id),
        }


class TestHttpOwnershipIsolation:
    def test_owner_can_read_their_own_entry(self, client, two_businesses_with_a_real_entry):
        r = client.get(
            f"/api/v1/loan-book/entries/{two_businesses_with_a_real_entry['entry_id']}",
            headers={"Authorization": f"Bearer {two_businesses_with_a_real_entry['token_a']}"},
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["outstandingAmount"]["minor_units"] == 75000

    def test_other_business_cannot_read_via_real_http(self, client, two_businesses_with_a_real_entry):
        r = client.get(
            f"/api/v1/loan-book/entries/{two_businesses_with_a_real_entry['entry_id']}",
            headers={"Authorization": f"Bearer {two_businesses_with_a_real_entry['token_b']}"},
        )
        assert r.status_code == 404

    def test_other_business_cannot_pay_via_real_http(self, client, two_businesses_with_a_real_entry):
        r = client.post(
            f"/api/v1/loan-book/entries/{two_businesses_with_a_real_entry['entry_id']}/payments",
            json={"amountCents": 10000},
            headers={"Authorization": f"Bearer {two_businesses_with_a_real_entry['token_b']}"},
        )
        assert r.status_code == 404

    def test_other_business_cannot_delete_via_real_http(self, client, two_businesses_with_a_real_entry):
        r = client.delete(
            f"/api/v1/loan-book/entries/{two_businesses_with_a_real_entry['entry_id']}",
            headers={"Authorization": f"Bearer {two_businesses_with_a_real_entry['token_b']}"},
        )
        assert r.status_code == 404

    def test_no_token_is_401(self, client, two_businesses_with_a_real_entry):
        r = client.get(f"/api/v1/loan-book/entries/{two_businesses_with_a_real_entry['entry_id']}")
        assert r.status_code == 401