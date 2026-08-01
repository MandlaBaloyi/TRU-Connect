"""
Refresh Token Model.
 -- Refresh Token


DESIGN
------
Stores a HASH of each issued refresh token's JWT ID (jti), never the
token itself -- revocation and rotation only need to know "is this jti
still valid", not the token's content, and access tokens remain fully
stateless ( rule: "Access Tokens remain stateless"). Only refresh
tokens are tracked here.

WHY IT EXISTS
-------------
flask_jwt_extended's tokens are stateless by default -- once issued, an
access or refresh token is valid until it expires, with no way to
invalidate it early. That's fine for short-lived access tokens, but
refresh tokens live much longer (docs/10, JWT_REFRESH_TOKEN_EXPIRES_DAYS)
and MUST be revocable (logout, password reset, suspected compromise).
This table is what makes that possible.

INTEGRATION WITH PREVIOUS STEPS
--------------------------------
Every refresh token issued by AuthService._issue_tokens  now
also creates a row here  addition to that method. user_id
references the User model (Step 5) directly.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "auth"}  #  Links table to the auth domain schema

    user_id = db.Column(
        UUID(as_uuid=True), 
        db.ForeignKey("auth.users.id", ondelete="CASCADE"),  # <-- UPDATED: Added 'auth.' schema prefix
        nullable=False, 
        index=True
    )
    jti_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Reserved for future multi-device/session-management support
    #  "Prepared architecture for future Device IDs, Session IDs,
    # IP Address logging") -- not yet populated by any current caller.
    device_id = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)

    def is_valid(self) -> bool:
        """True if this token has not been revoked and has not expired.
        Used defensively in addition to the JWT's own expiry check, so a
        token can be invalidated immediately (logout, password reset)
        rather than only at its natural expiry."""
        from src.core.base_model import utcnow

        if self.revoked_at is not None:
            return False
        return self.expires_at > utcnow()