"""
Password Reset Token Model.
Ref: continuation master prompt (Phase 3), Step 14 -- Forgot Password.

DESIGN
------
token_hash stores a SHA-256 hash of a cryptographically random token
(generated with Python's `secrets` module, not `random` -- reset tokens
must be unguessable). Same rationale as RefreshToken/OTPVerification:
never store a value in the database that could itself be replayed if
leaked.

is_used enforces the Step 14 rule "Single-use reset tokens" / "Prevent
token replay" -- once a reset succeeds, this flips to True and the same
token can never be used again, independent of whether it has expired
yet.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class PasswordResetToken(BaseModel):
    __tablename__ = "password_reset_tokens"

    user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    is_used = db.Column(db.Boolean, nullable=False, default=False)

    def is_valid(self) -> bool:
        from src.core.base_model import utcnow

        if self.is_used:
            return False
        return self.expires_at > utcnow()
