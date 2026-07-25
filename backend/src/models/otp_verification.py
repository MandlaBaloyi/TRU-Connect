"""
OTP Verification Model.
Ref: continuation master prompt (Phase 3), Step 13 -- OTP Verification.

DESIGN
------
otp_code_hash stores a SHA-256 hash of the (short-lived, single-use,
numeric) OTP code, never the plaintext code, for the same reason
passwords are hashed -- if the database leaks, stored codes should not
be directly usable. bcrypt is not used here (unlike passwords): OTPs are
low-entropy by design (6 digits) and short-lived, so bcrypt's
deliberately-slow hashing buys little extra protection over a fast hash
combined with expiry + attempt limiting, which are the real defenses
against an OTP being guessed.

attempts / max_attempts implement the Step 13 business rule "OTP
attempts are limited" -- exceeding max_attempts invalidates the code
even if it hasn't expired yet, requiring the user to request a new one.

purpose distinguishes email vs phone verification so the same table
supports both without needing two near-identical tables (Step 13:
"Support Email verification, Phone verification... without redesign").
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class OTPPurpose(str, enum.Enum):
    EMAIL_VERIFICATION = "email_verification"
    PHONE_VERIFICATION = "phone_verification"


class OTPVerification(BaseModel):
    __tablename__ = "otp_verifications"

    user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purpose = db.Column(db.Enum(OTPPurpose, name="otp_purpose"), nullable=False)
    destination = db.Column(db.String(255), nullable=False)  # the email/phone the code was sent to

    otp_code_hash = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    attempts = db.Column(db.Integer, nullable=False, default=0)
    max_attempts = db.Column(db.Integer, nullable=False, default=5)

    is_used = db.Column(db.Boolean, nullable=False, default=False)

    def is_expired(self) -> bool:
        from src.core.base_model import utcnow

        return self.expires_at <= utcnow()

    def has_attempts_remaining(self) -> bool:
        return self.attempts < self.max_attempts
