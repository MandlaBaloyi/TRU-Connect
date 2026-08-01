"""
Password Reset Token Repository.
 -- repositories ONLY talk to SQLAlchemy;
expiry/replay/enumeration-protection rules live in
src/services/password_reset_service.py.
"""
from __future__ import annotations

from typing import Optional

from src.extensions import db
from src.domains.auth.models.password_reset_token import PasswordResetToken


class PasswordResetRepository:
    @staticmethod
    def create(user_id, token_hash: str, expires_at) -> PasswordResetToken:
        record = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def get_by_token_hash(token_hash: str) -> Optional[PasswordResetToken]:
        return PasswordResetToken.query.filter_by(token_hash=token_hash, is_deleted=False).first()

    @staticmethod
    def mark_used(record: PasswordResetToken) -> PasswordResetToken:
        record.is_used = True
        db.session.commit()
        return record
