"""
API Key Repository.

SQLAlchemy only -- what a key MEANS (is it live, may it do this, when do
we bother recording that it was used) lives in api_key_service.py.
"""
from __future__ import annotations

from typing import Optional

from src.core.base_model import utcnow
from src.domains.auth.api_keys.models.api_key import ApiKey
from src.extensions import db


class ApiKeyRepository:
    @staticmethod
    def create(user_id, name: str, prefix: str, key_hash: str, scopes: list, expires_at=None) -> ApiKey:
        key = ApiKey(
            user_id=user_id,
            name=name,
            prefix=prefix,
            key_hash=key_hash,
            scopes=sorted(set(scopes)),
            expires_at=expires_at,
        )
        db.session.add(key)
        db.session.commit()
        return key

    @staticmethod
    def get_by_prefix(prefix: str) -> Optional[ApiKey]:
        """Authentication looks a key up BY PREFIX, then compares
        hashes, rather than querying on key_hash directly.

        Two reasons, and the second is the real one:

        1. A failed attempt can be audited usefully. "Key tck_9f3a2b71
           was rejected" tells a supplier which of their four servers is
           misconfigured; "some key was rejected" tells them nothing. A
           hash lookup that misses has nothing to name.

        2. The comparison then happens in Python, where it can be done
           in constant time (hmac.compare_digest in the service). A
           database equality check on the hash is not constant-time and
           its timing is observable.

        Deliberately does NOT filter on is_deleted / revoked_at /
        expires_at. The service needs to distinguish "no such key" from
        "a key that is no longer valid" -- for the audit trail, not for
        the response, which says the same thing either way.
        """
        return ApiKey.query.filter_by(prefix=prefix).first()

    @staticmethod
    def list_for_user(user_id) -> list:
        """Newest first. Includes revoked keys, on purpose: a supplier
        looking at this screen is often trying to confirm that a key
        they killed is in fact dead, and a row that vanishes cannot
        confirm anything."""
        return (
            ApiKey.query.filter_by(user_id=user_id, is_deleted=False)
            .order_by(ApiKey.created_at.desc())
            .all()
        )

    @staticmethod
    def get_for_user(user_id, key_id) -> Optional[ApiKey]:
        """Scoped to the owner in the QUERY rather than fetched and then
        checked. A revoke endpoint that loads by id and compares
        afterwards is one forgotten `if` away from letting any supplier
        revoke any other supplier's key."""
        return ApiKey.query.filter_by(id=key_id, user_id=user_id, is_deleted=False).first()

    @staticmethod
    def count_active_for_user(user_id) -> int:
        return ApiKey.query.filter_by(user_id=user_id, is_deleted=False, revoked_at=None).count()

    @staticmethod
    def revoke(key: ApiKey) -> ApiKey:
        key.revoked_at = utcnow()
        db.session.commit()
        return key

    @staticmethod
    def touch_last_used(key: ApiKey) -> None:
        """Records that this key was just used.

        NEVER RAISES, and rolls back only its own write on failure. This
        is bookkeeping on the way to somebody's actual API call -- a
        failed heartbeat must not turn a working integration into a 500.
        Same rule, and the same reasoning, as _touch_last_active in
        core/decorators.py.
        """
        try:
            key.last_used_at = utcnow()
            db.session.commit()
        except Exception:  # noqa: BLE001
            try:
                db.session.rollback()
            except Exception:  # noqa: BLE001
                pass
