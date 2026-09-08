"""
API key tests (V2 2.10) -- the machine door.

THE PROPERTIES WORTH TESTING here are the ones whose failure is silent:

  1. The raw key is returned ONCE and is not recoverable afterwards --
     not from the list endpoint, not from the database.
  2. What is stored is a hash, not the key.
  3. Scopes are actually enforced, not merely recorded. A scope system
     that stores permissions and never checks them looks identical from
     the portal and grants everything.
  4. A revoked key stops working immediately.
  5. One supplier cannot touch another's keys.
  6. A key belonging to a deactivated account stops working, even though
     the key itself is still perfectly valid.

Number 6 is the one that would otherwise be found in production.
"""
from __future__ import annotations

import hashlib

import pytest
from flask import g

from src.core.exceptions import ApiKeyScopeError, InvalidApiKeyError
from src.domains.auth.api_keys import scopes as scope_vocab
from src.domains.auth.api_keys.models.api_key import ApiKey
from src.domains.auth.api_keys.services.api_key_service import (
    MAX_ACTIVE_KEYS_PER_USER,
    ApiKeyService,
)
from src.domains.auth.models.user import AccountStatus, UserRole, VerificationStatus
from src.extensions import db

PASSWORD = "Abcd1234!"
KEYS = "/api/v1/supplier/api-keys"


@pytest.fixture()
def supplier(make_user):
    user = make_user(
        "keys-supplier@example.com",
        password=PASSWORD,
        role=UserRole.SUPPLIER,
        verification_status=VerificationStatus.VERIFIED,
        account_status=AccountStatus.ACTIVE,
        business_name="MacMan Wholesalers",
    )
    db.session.commit()
    return user


@pytest.fixture()
def other_supplier(make_user):
    user = make_user(
        "rival@example.com",
        password=PASSWORD,
        role=UserRole.SUPPLIER,
        verification_status=VerificationStatus.VERIFIED,
        account_status=AccountStatus.ACTIVE,
        business_name="Rival Distributors",
    )
    db.session.commit()
    return user


@pytest.fixture()
def business(make_user):
    user = make_user(
        "keys-business@example.com",
        password=PASSWORD,
        role=UserRole.BUSINESS,
        verification_status=VerificationStatus.VERIFIED,
        account_status=AccountStatus.ACTIVE,
    )
    db.session.commit()
    return user


def _bearer(client, user):
    """A mobile-style token. Used because it is the shortest way to an
    authenticated request in a test -- the endpoints themselves are
    reached from the portal with a cookie, and both arrive at the same
    @fully_authenticated."""
    response = client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": PASSWORD}
    )
    return {"Authorization": f"Bearer {response.get_json()['data']['tokens']['access_token']}"}


# ---------------------------------------------------------------------
# Minting
# ---------------------------------------------------------------------

def test_create_returns_the_key_once_and_stores_only_a_hash(client, supplier):
    response = client.post(
        KEYS,
        headers=_bearer(client, supplier),
        json={"name": "Warehouse sync", "scopes": [scope_vocab.CATALOGUE_WRITE]},
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    raw = data["key"]
    assert raw.startswith("tck_")

    # The database must not hold anything that can be presented as a
    # credential -- only the SHA-256 of one.
    row = ApiKey.query.filter_by(prefix=data["apiKey"]["prefix"]).one()
    assert row.key_hash == hashlib.sha256(raw.encode()).hexdigest()
    assert raw not in str(row.__dict__)

    # And the list view can never hand it back.
    listed = client.get(KEYS, headers=_bearer(client, supplier)).get_json()["data"]["keys"]
    assert len(listed) == 1
    assert raw not in str(listed)
    assert listed[0]["prefix"] == data["apiKey"]["prefix"]


def test_generated_key_has_exactly_three_underscore_separated_parts(client, supplier):
    """The format is `tck_<prefix>_<secret>` and authenticate() splits on
    "_" expecting three parts. A secret drawn from an alphabet that
    contains "_" would produce four and be rejected as malformed --
    intermittently, depending on the random bytes. This is why the
    secret is hex.

    The hex assertion is the one that actually proves it: sampling a
    handful of keys could pass by luck, but an alphabet with no "_" in
    it cannot produce one at any sample size."""
    for _ in range(MAX_ACTIVE_KEYS_PER_USER):
        _, raw = ApiKeyService.issue(supplier.id, "n", [scope_vocab.CATALOGUE_READ])
        parts = raw.split("_")
        assert len(parts) == 3
        assert parts[0] == "tck"
        assert all(c in "0123456789abcdef" for c in parts[1] + parts[2])
        assert len(parts[2]) == 64


def test_unknown_scope_is_named_in_the_error(client, supplier):
    response = client.post(
        KEYS,
        headers=_bearer(client, supplier),
        json={"name": "Typo", "scopes": ["catalogue:wrote"]},
    )
    assert response.status_code == 422
    assert "catalogue:wrote" in str(response.get_json())


def test_key_count_is_capped(client, supplier):
    for i in range(MAX_ACTIVE_KEYS_PER_USER):
        ApiKeyService.issue(supplier.id, f"key {i}", [scope_vocab.CATALOGUE_READ])

    response = client.post(
        KEYS,
        headers=_bearer(client, supplier),
        json={"name": "one too many", "scopes": [scope_vocab.CATALOGUE_READ]},
    )
    assert response.status_code == 409


def test_business_cannot_create_a_key(client, business):
    """Keys are the supplier integration door. A business has no
    catalogue to push."""
    response = client.post(
        KEYS,
        headers=_bearer(client, business),
        json={"name": "nope", "scopes": [scope_vocab.CATALOGUE_READ]},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------
# Authenticating
# ---------------------------------------------------------------------

def test_a_valid_key_authenticates(app, supplier):
    _, raw = ApiKeyService.issue(supplier.id, "Sync", [scope_vocab.CATALOGUE_WRITE])
    key = ApiKeyService.authenticate(raw)
    assert str(key.user_id) == str(supplier.id)


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "",
        "not-a-key",
        "tck_short",
        "tck_deadbeef_" + "0" * 64,  # right shape, wrong secret
    ],
)
def test_bad_keys_all_fail_the_same_way(app, supplier, bad):
    """One error for every failure mode. Distinguishing them would tell
    an unauthenticated caller which prefixes exist."""
    ApiKeyService.issue(supplier.id, "Sync", [scope_vocab.CATALOGUE_READ])
    with pytest.raises(InvalidApiKeyError):
        ApiKeyService.authenticate(bad)


def test_scope_is_enforced_not_merely_recorded(app, supplier):
    _, raw = ApiKeyService.issue(supplier.id, "Read only", [scope_vocab.CATALOGUE_READ])
    key = ApiKeyService.authenticate(raw)

    ApiKeyService.require_scopes(key, [scope_vocab.CATALOGUE_READ])

    with pytest.raises(ApiKeyScopeError):
        ApiKeyService.require_scopes(key, [scope_vocab.CATALOGUE_WRITE])


def test_scope_error_names_what_was_missing(app, supplier):
    """The caller is authenticated, so telling them costs nothing and
    turns a support email into a self-service fix."""
    _, raw = ApiKeyService.issue(supplier.id, "Read only", [scope_vocab.CATALOGUE_READ])
    key = ApiKeyService.authenticate(raw)

    with pytest.raises(ApiKeyScopeError) as exc:
        ApiKeyService.require_scopes(key, [scope_vocab.ORDERS_WRITE])

    assert scope_vocab.ORDERS_WRITE in exc.value.data["required"]
    assert scope_vocab.CATALOGUE_READ in exc.value.data["granted"]


def test_last_used_is_recorded(app, supplier):
    record, raw = ApiKeyService.issue(supplier.id, "Sync", [scope_vocab.CATALOGUE_READ])
    assert record.last_used_at is None

    ApiKeyService.authenticate(raw)

    assert record.last_used_at is not None


# ---------------------------------------------------------------------
# Revoking
# ---------------------------------------------------------------------

def test_revoked_key_stops_working_immediately(client, supplier):
    record, raw = ApiKeyService.issue(supplier.id, "Sync", [scope_vocab.CATALOGUE_READ])

    response = client.delete(f"{KEYS}/{record.id}", headers=_bearer(client, supplier))
    assert response.status_code == 200

    with pytest.raises(InvalidApiKeyError):
        ApiKeyService.authenticate(raw)


def test_revoking_twice_is_idempotent(client, supplier):
    record, _ = ApiKeyService.issue(supplier.id, "Sync", [scope_vocab.CATALOGUE_READ])
    headers = _bearer(client, supplier)

    assert client.delete(f"{KEYS}/{record.id}", headers=headers).status_code == 200
    assert client.delete(f"{KEYS}/{record.id}", headers=headers).status_code == 200


def test_a_supplier_cannot_revoke_another_suppliers_key(client, supplier, other_supplier):
    record, raw = ApiKeyService.issue(other_supplier.id, "Theirs", [scope_vocab.CATALOGUE_READ])

    response = client.delete(f"{KEYS}/{record.id}", headers=_bearer(client, supplier))

    assert response.status_code == 404
    # And it still works, which is the half that would actually hurt.
    assert ApiKeyService.authenticate(raw) is not None


def test_a_supplier_only_sees_their_own_keys(client, supplier, other_supplier):
    ApiKeyService.issue(supplier.id, "Mine", [scope_vocab.CATALOGUE_READ])
    ApiKeyService.issue(other_supplier.id, "Theirs", [scope_vocab.CATALOGUE_READ])

    listed = client.get(KEYS, headers=_bearer(client, supplier)).get_json()["data"]["keys"]

    assert [k["name"] for k in listed] == ["Mine"]


def test_revoked_keys_remain_visible_in_the_list(client, supplier):
    """A row that vanishes cannot confirm that the key is dead, which is
    the main reason someone opens this screen."""
    record, _ = ApiKeyService.issue(supplier.id, "Old sync", [scope_vocab.CATALOGUE_READ])
    client.delete(f"{KEYS}/{record.id}", headers=_bearer(client, supplier))

    listed = client.get(KEYS, headers=_bearer(client, supplier)).get_json()["data"]["keys"]

    assert len(listed) == 1
    assert listed[0]["active"] is False
    assert listed[0]["revokedAt"] is not None


# ---------------------------------------------------------------------
# The decorator
# ---------------------------------------------------------------------

def test_decorator_rejects_a_key_from_a_deactivated_account(app, client, supplier):
    """The KEY is valid; the ACCOUNT is not. A supplier deactivated this
    morning still holds keys minted last year, and they must stop
    working the moment the account does."""
    from src.core.decorators import api_key_required

    _, raw = ApiKeyService.issue(supplier.id, "Sync", [scope_vocab.CATALOGUE_READ])

    @api_key_required(scope_vocab.CATALOGUE_READ)
    def _protected():
        return "ok"

    app.add_url_rule("/_test/keyed", "keyed_probe", _protected)

    ok = client.get("/_test/keyed", headers={"Authorization": f"Bearer {raw}"})
    assert ok.status_code == 200

    supplier.account_status = AccountStatus.DEACTIVATED
    db.session.commit()

    blocked = client.get("/_test/keyed", headers={"Authorization": f"Bearer {raw}"})
    assert blocked.status_code == 403


def test_decorator_exposes_the_owner_on_g(app, client, supplier):
    from src.core.decorators import api_key_required

    _, raw = ApiKeyService.issue(supplier.id, "Sync", [scope_vocab.CATALOGUE_READ])
    seen = {}

    @api_key_required(scope_vocab.CATALOGUE_READ)
    def _probe():
        seen["user_id"] = g.api_key_user_id
        return "ok"

    app.add_url_rule("/_test/keyed-g", "keyed_g_probe", _probe)
    client.get("/_test/keyed-g", headers={"Authorization": f"Bearer {raw}"})

    assert seen["user_id"] == str(supplier.id)
