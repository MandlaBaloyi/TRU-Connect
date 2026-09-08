"""
API Key Service -- minting, authenticating and revoking machine
credentials (V2 2.10).

THE ONE RULE THIS FILE EXISTS TO ENFORCE: the raw key is visible in
exactly one place, the return value of issue(), and is never written
anywhere we can read back. Not the database, not the audit trail, not
a log line. Everything else here is in service of that.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta
from typing import Optional, Tuple

from src.core.base_model import utcnow
from src.core.exceptions import (
    ApiKeyScopeError,
    ConflictError,
    InvalidApiKeyError,
    NotFoundError,
    ValidationError,
)
from src.domains.auth.api_keys import scopes as scope_vocab
from src.domains.auth.api_keys.models.api_key import ApiKey
from src.domains.auth.api_keys.repositories.api_key_repository import ApiKeyRepository
from src.shared.audit import audit

# tck = TruConnect Key. A recognisable, greppable prefix is not
# decoration: it is what lets a secret scanner (GitHub's, or ours one
# day) spot this string in a commit and tell the owner before somebody
# else finds it. Every platform that has been burned by keys in public
# repos ended up here.
KEY_PREFIX_LABEL = "tck"

# 8 hex characters of public identifier. Enough that collisions are not
# a practical concern at any supplier count we will ever have, short
# enough to read down a list.
PREFIX_RANDOM_BYTES = 4

# 32 bytes -> 64 HEX characters. Far past the point where brute force is
# the attack anyone would choose; see the model's docstring on why this
# entropy is what justifies a fast hash.
#
# HEX, NOT token_urlsafe, AND THAT IS NOT A STYLE CHOICE. url-safe
# base64 draws from an alphabet that includes "_" -- the very character
# this key format uses as its separator. A secret that happened to
# contain one would parse into four parts instead of three and be
# rejected as malformed: a key that fails perhaps a third of the time,
# at random, depending on which bytes the CSPRNG handed out. Hex has no
# separator character in its alphabet, so the format cannot collide with
# its own contents.
SECRET_RANDOM_BYTES = 32

# A cap, because an unbounded list of live credentials per account is
# how a compromised portal session quietly mints itself persistence.
# Ten is well above what any real integration needs and low enough that
# the list stays readable.
MAX_ACTIVE_KEYS_PER_USER = 10

# last_used_at is a "when did this integration last run" signal, not an
# access log. Writing a row on every request would double the write cost
# of the cheapest read endpoint for information nobody reads at that
# resolution. Five minutes is finer than any question this column
# answers.
LAST_USED_THROTTLE_MINUTES = 5


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class ApiKeyService:
    # ------------------------------------------------------------------
    # Minting
    # ------------------------------------------------------------------

    @staticmethod
    def issue(
        user_id,
        name: str,
        requested_scopes,
        expires_in_days: Optional[int] = None,
    ) -> Tuple[ApiKey, str]:
        """Creates a key and returns (record, raw_key).

        THE RAW KEY IS RETURNED, NOT STORED. This is the only moment it
        exists in a readable form anywhere in the system. The caller --
        the route -- puts it in one response and forgets it. There is
        deliberately no way to ask for it again: an endpoint that could
        re-reveal a key would make every path that can read the database
        a path that can read live credentials, which is precisely what
        hashing them was for.
        """
        name = (name or "").strip()
        if not name:
            raise ValidationError("Give the key a name so you can tell it apart later.")
        if len(name) > 80:
            raise ValidationError("Key name must be 80 characters or fewer.")

        requested = sorted(set(requested_scopes or []))
        if not requested:
            raise ValidationError("Choose at least one permission for this key.")

        unknown = scope_vocab.unknown_scopes(requested)
        if unknown:
            # Named explicitly. A caller who mistyped "catalogue:wrote"
            # needs to see the typo, and these are our own scope names,
            # not a secret.
            raise ValidationError(f"Unknown permissions: {', '.join(unknown)}.")

        if ApiKeyRepository.count_active_for_user(user_id) >= MAX_ACTIVE_KEYS_PER_USER:
            raise ConflictError(
                f"You already have {MAX_ACTIVE_KEYS_PER_USER} active keys. "
                "Revoke one you no longer use before creating another."
            )

        expires_at = None
        if expires_in_days is not None:
            if expires_in_days < 1 or expires_in_days > 730:
                raise ValidationError("Expiry must be between 1 and 730 days.")
            expires_at = utcnow() + timedelta(days=expires_in_days)

        prefix = f"{KEY_PREFIX_LABEL}_{secrets.token_hex(PREFIX_RANDOM_BYTES)}"
        secret = secrets.token_hex(SECRET_RANDOM_BYTES)
        raw_key = f"{prefix}_{secret}"

        key = ApiKeyRepository.create(
            user_id=user_id,
            name=name,
            prefix=prefix,
            key_hash=_hash_key(raw_key),
            scopes=requested,
            expires_at=expires_at,
        )

        audit.log_api_key_created(str(user_id), str(key.id), name, requested)
        return key, raw_key

    # ------------------------------------------------------------------
    # Authenticating
    # ------------------------------------------------------------------

    @staticmethod
    def authenticate(raw_key: Optional[str], ip_address: Optional[str] = None) -> ApiKey:
        """Resolves a presented key to its record, or raises.

        EVERY FAILURE RAISES THE SAME ERROR. Malformed, unknown,
        revoked, expired -- one InvalidApiKeyError, one message. Telling
        an unauthenticated caller which it was confirms that a key
        exists, or once did, in exchange for a debugging convenience the
        legitimate owner can get from their own portal screen, where we
        know who they are. The audit row records the real reason; the
        response does not.
        """
        if not raw_key or not raw_key.startswith(f"{KEY_PREFIX_LABEL}_"):
            audit.log_api_key_auth_failed(None, ip_address, "malformed")
            raise InvalidApiKeyError("Invalid API key.")

        parts = raw_key.split("_")
        if len(parts) != 3 or not parts[1] or not parts[2]:
            audit.log_api_key_auth_failed(None, ip_address, "malformed")
            raise InvalidApiKeyError("Invalid API key.")

        prefix = f"{parts[0]}_{parts[1]}"
        key = ApiKeyRepository.get_by_prefix(prefix)

        if key is None:
            audit.log_api_key_auth_failed(prefix, ip_address, "unknown_prefix")
            raise InvalidApiKeyError("Invalid API key.")

        # CONSTANT TIME, not ==. A plain string comparison returns as
        # soon as it finds a differing character, so how long it took
        # leaks how much of the hash was right -- enough, over many
        # attempts, to reconstruct it a character at a time. This is
        # cheap to do correctly and awkward to notice when done wrong.
        if not hmac.compare_digest(key.key_hash, _hash_key(raw_key)):
            audit.log_api_key_auth_failed(prefix, ip_address, "hash_mismatch")
            raise InvalidApiKeyError("Invalid API key.")

        if not key.is_active():
            reason = "revoked" if key.revoked_at is not None else "expired_or_deleted"
            audit.log_api_key_auth_failed(prefix, ip_address, reason)
            raise InvalidApiKeyError("Invalid API key.")

        ApiKeyService._touch(key)
        return key

    @staticmethod
    def _touch(key: ApiKey) -> None:
        """Throttled last-used write. See LAST_USED_THROTTLE_MINUTES."""
        now = utcnow()
        if key.last_used_at is not None and now - key.last_used_at < timedelta(
            minutes=LAST_USED_THROTTLE_MINUTES
        ):
            return
        ApiKeyRepository.touch_last_used(key)

    @staticmethod
    def require_scopes(key: ApiKey, required) -> None:
        """Raises ApiKeyScopeError -- NOT InvalidApiKeyError -- when a
        valid key lacks a permission.

        The distinction matters because this caller is authenticated: we
        know whose key this is, so naming the missing scope leaks
        nothing they do not already own, and it is the difference
        between a support email and a self-service fix. It is also the
        single most common integration mistake there is.
        """
        if not key.has_scopes(required):
            audit.log_api_key_scope_denied(
                str(key.user_id), str(key.id), list(required), list(key.scopes or [])
            )
            raise ApiKeyScopeError(
                "This API key does not have permission to do that.",
                data={"required": sorted(required), "granted": sorted(key.scopes or [])},
            )

    # ------------------------------------------------------------------
    # Managing (from the portal)
    # ------------------------------------------------------------------

    @staticmethod
    def list_keys(user_id) -> list:
        return ApiKeyRepository.list_for_user(user_id)

    @staticmethod
    def revoke(user_id, key_id) -> ApiKey:
        """Revocation is immediate and one-way.

        NO UN-REVOKE, deliberately. Someone revokes a key because they
        believe it leaked; if they were right, the key is in someone
        else's hands and a restore button hands it back. Making a new
        key costs thirty seconds and is the correct response to every
        situation where un-revoking sounds appealing.
        """
        key = ApiKeyRepository.get_for_user(user_id, key_id)
        if key is None:
            raise NotFoundError("API key not found.")
        if key.revoked_at is not None:
            # Idempotent rather than a 409. The supplier's intent was
            # "make sure this key is dead", and it is.
            return key

        ApiKeyRepository.revoke(key)
        audit.log_api_key_revoked(str(user_id), str(key.id))
        return key
