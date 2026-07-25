"""
Refresh Token Repository.
Ref: continuation master prompt -- repositories ONLY talk to SQLAlchemy;
no business rules here (rotation/revocation policy lives in
src/services/auth_service.py).
"""
from __future__ import annotations

from typing import Optional

from src.core.base_model import utcnow
from src.extensions import db
from src.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    @staticmethod
    def create(user_id, jti_hash: str, expires_at, device_id: str | None = None, ip_address: str | None = None) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            jti_hash=jti_hash,
            expires_at=expires_at,
            device_id=device_id,
            ip_address=ip_address,
        )
        db.session.add(token)
        db.session.commit()
        return token

    @staticmethod
    def get_by_jti_hash(jti_hash: str) -> Optional[RefreshToken]:
        return RefreshToken.query.filter_by(jti_hash=jti_hash, is_deleted=False).first()

    @staticmethod
    def revoke(token: RefreshToken) -> RefreshToken:
        token.revoked_at = utcnow()
        db.session.commit()
        return token

    @staticmethod
    def revoke_all_for_user(user_id) -> int:
        """Revokes every currently-valid refresh token for a user (used
        by password reset -- Step 14 -- and available for a future
        explicit "logout all devices" endpoint -- Step 12). Returns the
        number of tokens revoked."""
        tokens = RefreshToken.query.filter_by(user_id=user_id, revoked_at=None, is_deleted=False).all()
        now = utcnow()
        for token in tokens:
            token.revoked_at = now
        db.session.commit()
        return len(tokens)
