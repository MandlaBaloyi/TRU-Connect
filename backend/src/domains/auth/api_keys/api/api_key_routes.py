"""
API Key management routes -- the SUPPLIER-FACING half.

These are managed by a human, from the portal, with a normal session.
They are not the machine door itself: nothing here is called by an ERP.
A supplier signs in, creates a key, copies it into their system once,
and comes back only to see when it was last used or to kill it.

WHY THIS IS SESSION-AUTHENTICATED AND NOT KEY-AUTHENTICATED. A key must
never be able to mint another key. If it could, a single leaked
credential becomes permanent: revoke the one you know about and the
attacker still holds the three it quietly created. Key creation requires
a human who proved they own the account.
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import error_response, success_response
from src.domains.auth.api_keys import scopes as scope_vocab
from src.domains.auth.api_keys.schemas.api_key_schemas import CreateApiKeySchema
from src.domains.auth.api_keys.services.api_key_service import ApiKeyService

api_keys_bp = Blueprint("api_keys", __name__)

_create_schema = CreateApiKeySchema()


@api_keys_bp.get("/api-keys/scopes")
@fully_authenticated
@role_required("supplier")
def list_scopes():
    """The permission vocabulary, with its descriptions.

    SERVED FROM THE BACKEND rather than hard-coded in the portal, so the
    day a scope is added there is one place to add it and the UI cannot
    offer a permission the API does not enforce -- which is the failure
    that lets a supplier believe they granted something they did not.
    """
    return success_response(
        data={
            "scopes": [
                {"scope": scope, "description": scope_vocab.SCOPE_DESCRIPTIONS[scope]}
                for scope in scope_vocab.SCOPE_CHOICES
            ]
        }
    )


@api_keys_bp.get("/api-keys")
@fully_authenticated
@role_required("supplier")
def list_api_keys():
    keys = ApiKeyService.list_keys(get_jwt_identity())
    return success_response(data={"keys": [key.to_public_dict() for key in keys]})


@api_keys_bp.post("/api-keys")
@fully_authenticated
@role_required("supplier")
def create_api_key():
    """Creates a key and returns it IN FULL, exactly once.

    THE ONLY RESPONSE IN THE ENTIRE API THAT CONTAINS A RAW KEY. The
    `key` field below cannot be obtained again by any means -- not by
    re-reading the list, not by an admin, not from the database, which
    holds only a SHA-256 of it. The response says so, because a supplier
    who assumes they can look it up later will close the tab.
    """
    payload = request.get_json(silent=True) or {}
    try:
        data = _create_schema.load(payload)
    except MarshmallowValidationError as exc:
        errors = [f"{field}: {msgs}" for field, msgs in exc.messages.items()]
        return error_response(message="Validation failed", errors=errors, status_code=422)

    key, raw_key = ApiKeyService.issue(
        user_id=get_jwt_identity(),
        name=data["name"],
        requested_scopes=data["scopes"],
        expires_in_days=data.get("expires_in_days"),
    )

    return success_response(
        data={
            "key": raw_key,
            "warning": "Copy this key now. It cannot be shown again.",
            "apiKey": key.to_public_dict(),
        },
        message="API key created.",
        status_code=201,
    )


@api_keys_bp.delete("/api-keys/<uuid:key_id>")
@fully_authenticated
@role_required("supplier")
def revoke_api_key(key_id):
    """Kills a key immediately and permanently. Idempotent -- revoking
    an already-revoked key succeeds, because the caller's intent was
    "make sure this is dead" and it is."""
    key = ApiKeyService.revoke(get_jwt_identity(), key_id)
    return success_response(data=key.to_public_dict(), message="API key revoked.")
