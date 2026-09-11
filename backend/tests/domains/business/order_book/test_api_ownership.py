"""
HTTP-level ownership tests -- confirms isolation holds through the real
Flask route + JWT auth stack, not just when OrderBookService is called
directly as Python functions (see test_ownership.py for that layer).
Same shape as loan_book/test_api_ownership.py.

NOT YET RUN in this environment -- see conftest.py's docstring.
"""
from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token

from src.extensions import db


@pytest.fixture()
def two_businesses_with_a_real_order(app):
    import uuid
    from datetime import datetime, timezone

    from src.domains.auth.models.user import User, UserRole, VerificationStatus
    from src.domains.business.order_book.models.customer import OrderBookCustomer
    from src.domains.business.order_book.repositories.customer_repository import CustomerRepository
    from src.domains.business.order_book.services.order_book_service import OrderBookService, OrderLineItemInput
    from src.shared.finance import Money

    with app.app_context():
        business_a = User(
            id=uuid.uuid4(), email="ob-http-a@example.com", password_hash="x",
            role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED,
        )
        business_b = User(
            id=uuid.uuid4(), email="ob-http-b@example.com", password_hash="x",
            role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED,
        )
        db.session.add_all([business_a, business_b])
        db.session.commit()

        a_customer = OrderBookCustomer(
            id=uuid.uuid4(), business_id=business_a.id, name="A's customer",
            first_recorded_at=datetime.now(timezone.utc),
        )
        CustomerRepository.create(a_customer)
        db.session.commit()

        a_order = OrderBookService.create_order(
            business_a.id,
            [OrderLineItemInput(description="Kota", quantity=1, unit_price=Money(6500))],
            customer_id=a_customer.id,
        )

        return {
            "token_a": create_access_token(
                identity=str(business_a.id), additional_claims={"role": "business"}
            ),
            "token_b": create_access_token(
                identity=str(business_b.id), additional_claims={"role": "business"}
            ),
            "order_id": str(a_order.id),
        }


class TestHttpOwnershipIsolation:
    def test_owner_can_read_their_own_order(self, client, two_businesses_with_a_real_order):
        r = client.get(
            f"/api/v1/order-book/orders/{two_businesses_with_a_real_order['order_id']}",
            headers={"Authorization": f"Bearer {two_businesses_with_a_real_order['token_a']}"},
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["total"]["minor_units"] == 6500

    def test_other_business_cannot_read_via_real_http(self, client, two_businesses_with_a_real_order):
        r = client.get(
            f"/api/v1/order-book/orders/{two_businesses_with_a_real_order['order_id']}",
            headers={"Authorization": f"Bearer {two_businesses_with_a_real_order['token_b']}"},
        )
        assert r.status_code == 404

    def test_other_business_cannot_complete_via_real_http(self, client, two_businesses_with_a_real_order):
        r = client.post(
            f"/api/v1/order-book/orders/{two_businesses_with_a_real_order['order_id']}/complete",
            headers={"Authorization": f"Bearer {two_businesses_with_a_real_order['token_b']}"},
        )
        assert r.status_code == 404

    def test_other_business_cannot_delete_via_real_http(self, client, two_businesses_with_a_real_order):
        r = client.delete(
            f"/api/v1/order-book/orders/{two_businesses_with_a_real_order['order_id']}",
            headers={"Authorization": f"Bearer {two_businesses_with_a_real_order['token_b']}"},
        )
        assert r.status_code == 404

    def test_no_token_is_401(self, client, two_businesses_with_a_real_order):
        r = client.get(f"/api/v1/order-book/orders/{two_businesses_with_a_real_order['order_id']}")
        assert r.status_code == 401
