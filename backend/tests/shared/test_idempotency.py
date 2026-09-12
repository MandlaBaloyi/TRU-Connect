"""
Retrying a request must not do it twice (V2_13 §3.1).

THE FAILURE. A supplier's ERP posts a product, the connection times out
at fifteen seconds, and the ERP retries -- correctly, because it cannot
know whether we processed the first attempt. Without a key we create a
SECOND product, and nobody notices until the catalogue has doubled.

WHAT THESE TESTS PIN, in rough order of how much it would hurt to get
wrong:

  A RETRY CREATES NOTHING. The handler does not run; the stored
  response is replayed. This is the entire feature.

  THE SAME KEY WITH A DIFFERENT BODY IS REFUSED. Replaying the first
  response there would tell a caller that a request they never really
  made had succeeded -- a silent wrong answer, which is worse than an
  error.

  NO HEADER MEANS NO CHANGE. The feature is opt-in per request, which
  is what lets it be added to a live endpoint without the mobile app
  knowing anything about it.

  KEYS DO NOT LEAK BETWEEN CALLERS. Clients choose their own keys, so
  two suppliers picking the same UUID must not see each other's
  responses.
"""
from __future__ import annotations

import uuid

import pytest
from flask_jwt_extended import create_access_token

from src.domains.auth.models.user import UserRole, VerificationStatus
from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
from src.extensions import db
from src.shared.idempotency import service as idempotency
from src.shared.idempotency.models import IdempotencyKey

URL = "/api/v1/supplier-discovery/products"


@pytest.fixture()
def seller(make_user, db_session):
    """A verified supplier with a profile, able to create products."""
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    def _make(email="seller@example.com"):
        user = make_user(
            email, role=UserRole.SUPPLIER, verification_status=VerificationStatus.VERIFIED
        )
        db_session.commit()
        SupplierProfileRepository.get_or_create_for_supplier(user.id, default_name="Seller Co")
        db_session.commit()
        return user

    return _make


def _headers(app, user, key=None):
    with app.app_context():
        token = create_access_token(
            identity=str(user.id), additional_claims={"role": user.role.value}
        )
    headers = {"Authorization": f"Bearer {token}"}
    if key:
        headers["Idempotency-Key"] = key
    return headers


def _payload(name="Maize Meal 10kg"):
    return {
        "name": name,
        "category": ProductCategory.FOOD_GROCERY.value,
        # SNAKE_CASE, matching CreateProductSchema -- this endpoint's
        # request body is not camelCase even though its responses are.
        "price_cents": 8900,
        "selling_unit": ProductUnit.EACH.value,
    }


def _product_count():
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer

    return SupplierOffer.query.filter_by(is_deleted=False).count()


class TestTheFeatureItself:
    def test_a_retry_creates_nothing_and_replays_the_answer(self, client, app, db_session, seller):
        """THE WHOLE POINT. Same key, same body, twice."""
        user = seller()
        key = str(uuid.uuid4())
        headers = _headers(app, user, key)

        first = client.post(URL, json=_payload(), headers=headers)
        assert first.status_code in (200, 201)
        after_first = _product_count()

        second = client.post(URL, json=_payload(), headers=headers)

        assert second.status_code == first.status_code
        assert second.get_json() == first.get_json()
        assert _product_count() == after_first, "the retry created a second product"

    def test_without_a_key_nothing_changes(self, client, app, db_session, seller):
        """OPT-IN PER REQUEST. This is what lets the decorator be added
        to a live endpoint without the mobile app knowing about it --
        two identical posts with no key are two real products, exactly
        as before."""
        user = seller()
        headers = _headers(app, user)

        client.post(URL, json=_payload("No Key One"), headers=headers)
        before = _product_count()
        client.post(URL, json=_payload("No Key Two"), headers=headers)

        assert _product_count() == before + 1
        assert IdempotencyKey.query.count() == 0

    def test_the_same_key_with_a_different_body_is_refused(
        self, client, app, db_session, seller
    ):
        """A CLIENT BUG, SHOUTED ABOUT RATHER THAN HIDDEN. Replaying the
        first response here would tell the caller that a request they
        never really made had succeeded."""
        user = seller()
        key = str(uuid.uuid4())
        headers = _headers(app, user, key)

        client.post(URL, json=_payload("First Thing"), headers=headers)
        second = client.post(URL, json=_payload("A Completely Different Thing"), headers=headers)

        assert second.status_code == 422
        assert "different request" in second.get_json()["message"]


class TestScoping:
    def test_two_callers_may_use_the_same_key(self, client, app, db_session, seller):
        """Clients generate their own keys, so a collision between two
        suppliers is inevitable eventually -- and must not leak one
        caller's response to the other."""
        a = seller("a@example.com")
        b = seller("b@example.com")
        key = str(uuid.uuid4())

        first = client.post(URL, json=_payload("A's Product"), headers=_headers(app, a, key))
        second = client.post(URL, json=_payload("B's Product"), headers=_headers(app, b, key))

        assert first.status_code in (200, 201)
        assert second.status_code in (200, 201)
        assert first.get_json() != second.get_json()
        assert IdempotencyKey.query.count() == 2


class TestTheStoredRow:
    def test_an_in_flight_claim_blocks_a_second_request(self, app, db_session, seller):
        """Two simultaneous retries: the unique constraint arbitrates,
        and the loser is told rather than let through to do the work
        twice."""
        user = seller()
        key = str(uuid.uuid4())

        idempotency.claim(key, user.id, "POST /x", "hash-a")

        with pytest.raises(idempotency.IdempotencyInFlight):
            idempotency.claim(key, user.id, "POST /x", "hash-a")

    def test_a_5xx_releases_the_claim(self, app, db_session, seller):
        """WHERE WE DEPART FROM STRIPE, deliberately. A handler that
        raised rolled its transaction back, so there is no duplicate to
        protect against -- and caching a transient failure for 24 hours
        would leave the client's only recovery being to invent a new
        key, which is how duplicates get made."""
        user = seller()
        key = str(uuid.uuid4())

        row = idempotency.claim(key, user.id, "POST /x", "hash-a")
        idempotency.release(row)

        assert IdempotencyKey.query.filter_by(key=key).first() is None

    def test_a_completed_row_is_replayable_not_blocking(self, app, db_session, seller):
        user = seller()
        key = str(uuid.uuid4())

        row = idempotency.claim(key, user.id, "POST /x", "hash-a")
        idempotency.complete(row, 201, {"success": True, "data": {"id": "abc"}})

        again = idempotency.claim(key, user.id, "POST /x", "hash-a")
        assert again.is_complete
        assert again.status_code == 201
        assert again.response_body["data"]["id"] == "abc"

    def test_the_body_is_hashed_not_stored(self, app, db_session):
        """We only ever COMPARE the request, so keeping a copy of every
        body for a day would be a retention problem invented for no
        benefit."""
        digest = idempotency.fingerprint(b'{"secret":"value"}')

        assert len(digest) == 64
        assert "secret" not in digest


class TestExpiry:
    def test_the_sweep_removes_only_expired_rows(self, app, db_session, seller):
        from datetime import timedelta

        from src.core.base_model import utcnow
        from src.shared.idempotency.jobs import expiry_sweep

        user = seller()
        fresh = idempotency.claim(str(uuid.uuid4()), user.id, "POST /x", "h1")
        stale = idempotency.claim(str(uuid.uuid4()), user.id, "POST /y", "h2")
        stale.expires_at = utcnow() - timedelta(hours=1)
        db.session.commit()

        # IDS CAPTURED BEFORE THE SWEEP. Holding the ORM instance and
        # reading .id afterwards triggers a refresh of a row that is
        # gone, which raises ObjectDeletedError instead of failing the
        # assertion this test is actually about.
        fresh_id, stale_id = fresh.id, stale.id

        result = expiry_sweep.run()

        assert result.success
        assert result.count == 1
        assert IdempotencyKey.query.filter_by(id=fresh_id).first() is not None
        assert IdempotencyKey.query.filter_by(id=stale_id).first() is None
