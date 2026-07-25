#!/usr/bin/env python3
"""
================================================================================
 TRU CONNECT BACKEND
 Authentication Module -- Phase 3 Generator
 Steps 11-16: Refresh Token Management, Logout, OTP Verification,
              Forgot Password, Role Authorization, Test Suite
================================================================================

Per the continuation master prompt, this completes the Authentication
Module (Steps 11-16), integrating with the already-approved Steps 1-10.

WHAT THIS SCRIPT WRITES (new files):
    src/models/refresh_token.py          Step 11
    src/models/otp_verification.py       Step 13
    src/models/password_reset_token.py   Step 14
    src/repositories/refresh_token_repository.py
    src/repositories/otp_repository.py
    src/repositories/password_reset_repository.py
    src/utils/otp.py                     OTP generation/hashing helpers
    src/schemas/otp_schemas.py
    src/schemas/password_reset_schemas.py
    src/services/otp_service.py
    src/services/password_reset_service.py

WHAT THIS SCRIPT REWRITES (existing Steps 7-10 files that Steps 11-16
genuinely need to extend -- NOT a "regenerate the foundation" violation;
Step 11 explicitly requires refresh-token rotation/persistence inside
the existing _issue_tokens/refresh flow, Step 12 requires logout to
revoke, and new routes must be registered):
    src/services/auth_service.py   adds refresh-token persistence,
                                    rotation, and revocation-aware
                                    refresh/logout; registration/login
                                    business logic UNCHANGED
    src/api/auth_routes.py         adds OTP + forgot/reset-password
                                    routes; enhances /refresh and
                                    /logout; register/login routes
                                    UNCHANGED
    src/core/decorators.py         adds permission_required() alongside
                                    the existing role_required()
                                    (untouched)
    tests/test_auth.py             extended with Steps 11-16 coverage,
                                    Steps 5-10 tests UNCHANGED

WHAT THIS SCRIPT INTEGRATES (targeted edit, same pattern as Phase 2):
    src/models/__init__.py   imports the 3 new models for Flask-Migrate

WHAT THIS SCRIPT NEVER TOUCHES:
    src/config.py, src/extensions.py, src/__init__.py, app.py,
    src/core/base_model.py, src/core/exceptions.py, src/core/responses.py,
    src/models/user.py, src/repositories/user_repository.py,
    src/schemas/auth_schemas.py, src/utils/security.py,
    requirements.txt, .env, migrations/**, docs/**, frontend/**

USAGE (run from the TRU_Connect root, or pass --root):

    python generate_backend_auth_module_phase3_.py --force
================================================================================
"""

import argparse
import os
import sys


BACKEND_REL = "backend"

FILES: dict = {}


# ==============================================================================
# Step 11 -- Refresh Token model
# ==============================================================================
# DESIGN: we never store the raw refresh token, only a SHA-256 hash of its
# JWT ID (jti) claim -- this lets us revoke/look up a specific token
# without the database ever holding a value that could itself be replayed
# if leaked. device_id/ip_address are included now (nullable) exactly as
# Step 11 asks ("Prepare architecture for future Device IDs, Session IDs,
# IP Address logging") even though nothing currently populates them with
# real values -- see the "Future multi-device support" note in
# auth_service.py for where they'd be filled in.

FILES[os.path.join("src", "models", "refresh_token.py")] = r'''"""
Refresh Token Model.
Ref: continuation master prompt (Phase 3), Step 11 -- Refresh Token
Management.

DESIGN
------
Stores a HASH of each issued refresh token's JWT ID (jti), never the
token itself -- revocation and rotation only need to know "is this jti
still valid", not the token's content, and access tokens remain fully
stateless (Step 12 rule: "Access Tokens remain stateless"). Only refresh
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
Every refresh token issued by AuthService._issue_tokens (Step 9) now
also creates a row here (Step 11 addition to that method). user_id
references the User model (Step 5) directly.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jti_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Reserved for future multi-device/session-management support
    # (Step 11: "Prepare architecture for future Device IDs, Session IDs,
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
'''


# ==============================================================================
# Step 13 -- OTP Verification model
# ==============================================================================

FILES[os.path.join("src", "models", "otp_verification.py")] = r'''"""
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
'''


# ==============================================================================
# Step 14 -- Password Reset Token model
# ==============================================================================

FILES[os.path.join("src", "models", "password_reset_token.py")] = r'''"""
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
'''

# ==============================================================================
# Step 11 -- Refresh Token Repository
# ==============================================================================

FILES[os.path.join("src", "repositories", "refresh_token_repository.py")] = r'''"""
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
'''


# ==============================================================================
# Step 13 -- OTP Repository
# ==============================================================================

FILES[os.path.join("src", "repositories", "otp_repository.py")] = r'''"""
OTP Repository.
Ref: continuation master prompt -- repositories ONLY talk to SQLAlchemy;
expiry/attempt/reuse business rules live in src/services/otp_service.py.
"""
from __future__ import annotations

from typing import Optional

from src.extensions import db
from src.models.otp_verification import OTPPurpose, OTPVerification


class OTPRepository:
    @staticmethod
    def create(user_id, purpose: OTPPurpose, destination: str, otp_code_hash: str, expires_at) -> OTPVerification:
        record = OTPVerification(
            user_id=user_id,
            purpose=purpose,
            destination=destination,
            otp_code_hash=otp_code_hash,
            expires_at=expires_at,
        )
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def get_latest_active(user_id, purpose: OTPPurpose) -> Optional[OTPVerification]:
        """Most recent, not-yet-used OTP for this user/purpose --
        requesting a new OTP does not delete older ones, but only the
        latest is ever considered valid for verification."""
        return (
            OTPVerification.query.filter_by(
                user_id=user_id, purpose=purpose, is_used=False, is_deleted=False
            )
            .order_by(OTPVerification.created_at.desc())
            .first()
        )

    @staticmethod
    def increment_attempts(record: OTPVerification) -> OTPVerification:
        record.attempts += 1
        db.session.commit()
        return record

    @staticmethod
    def mark_used(record: OTPVerification) -> OTPVerification:
        record.is_used = True
        db.session.commit()
        return record
'''


# ==============================================================================
# Step 14 -- Password Reset Token Repository
# ==============================================================================

FILES[os.path.join("src", "repositories", "password_reset_repository.py")] = r'''"""
Password Reset Token Repository.
Ref: continuation master prompt -- repositories ONLY talk to SQLAlchemy;
expiry/replay/enumeration-protection rules live in
src/services/password_reset_service.py.
"""
from __future__ import annotations

from typing import Optional

from src.extensions import db
from src.models.password_reset_token import PasswordResetToken


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
'''

# ==============================================================================
# Step 13 -- OTP generation/hashing helpers
# ==============================================================================

FILES[os.path.join("src", "utils", "otp.py")] = r'''"""
OTP generation and hashing helpers.
Ref: continuation master prompt (Phase 3), Step 13.

Kept separate from src/utils/security.py (which is specifically password
hashing/complexity) since OTP codes use a different, deliberately
different hashing approach -- see the design note in
src/models/otp_verification.py for why sha256 rather than bcrypt is used
here.
"""
from __future__ import annotations

import hashlib
import secrets


def generate_numeric_otp(length: int = 6) -> str:
    """Cryptographically random numeric OTP (uses `secrets`, not
    `random` -- `random` is not safe for anything security-sensitive)."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def verify_otp_hash(code: str, code_hash: str) -> bool:
    return hash_otp(code) == code_hash


def generate_reset_token() -> str:
    """Cryptographically random, URL-safe password reset token (Step 14:
    "Secure reset tokens" -- must be unguessable, unlike a 6-digit OTP)."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
'''


# ==============================================================================
# Step 13 -- OTP schemas
# ==============================================================================

FILES[os.path.join("src", "schemas", "otp_schemas.py")] = r'''"""
OTP request/verification schemas.
Ref: continuation master prompt (Phase 3), Step 13; matches
frontend/mobile/src/features/auth/types.ts (VerifyOtpPayload: destination
+ code) and docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1
(/auth/phone/request-otp, /auth/phone/verify-otp).
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class RequestOtpSchema(Schema):
    destination = fields.String(required=True, validate=validate.Length(min=1, max=255))


class VerifyOtpSchema(Schema):
    destination = fields.String(required=True, validate=validate.Length(min=1, max=255))
    code = fields.String(required=True, validate=validate.Length(equal=6))
'''


# ==============================================================================
# Step 14 -- Forgot/Reset Password schemas
# ==============================================================================

FILES[os.path.join("src", "schemas", "password_reset_schemas.py")] = r'''"""
Forgot/Reset password schemas.
Ref: continuation master prompt (Phase 3), Step 14;
docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1
(/auth/forgot-password, /auth/reset-password).
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate, validates, validates_schema
from marshmallow import ValidationError as MarshmallowValidationError

from src.utils.security import validate_password_complexity


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    token = fields.String(required=True)
    new_password = fields.String(required=True, load_only=True, data_key="newPassword")
    confirm_password = fields.String(required=True, load_only=True, data_key="confirmPassword")

    @validates("new_password")
    def validate_password_strength(self, value, **kwargs):
        errors = validate_password_complexity(value)
        if errors:
            raise MarshmallowValidationError(errors)

    @validates_schema
    def validate_cross_fields(self, data, **kwargs):
        if data.get("new_password") != data.get("confirm_password"):
            raise MarshmallowValidationError("Passwords do not match.", field_name="confirm_password")
'''

# ==============================================================================
# Steps 7-12 -- Authentication Service, REWRITTEN
# Registration and login business logic (Steps 7-8) are UNCHANGED from
# Phase 2. Steps 9-12 are extended: _issue_tokens now persists a
# RefreshToken row per issued refresh token (Step 11); refresh() now
# validates against that table and ROTATES (revokes the used token,
# issues a brand new pair) rather than just minting a new access token;
# logout() now actually revokes.
# ==============================================================================

FILES[os.path.join("src", "services", "auth_service.py")] = r'''"""
Authentication Service.
Ref: continuation master prompt, Steps 7-12. ALL business logic for
registration, login, JWT issuance, refresh-token rotation, and logout
lives here. Routes (src/api/auth_routes.py) call these methods and never
touch SQLAlchemy or JWT generation directly.

Steps 7-8 (register_business, register_supplier, login) are UNCHANGED
from the Phase 2 version. Steps 9-12 (_issue_tokens, refresh, logout) are
extended for refresh-token persistence, rotation, and revocation.
"""
from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jti

from src.core.base_model import utcnow
from src.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from src.models.user import User, UserRole
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.repositories.user_repository import UserRepository
from src.utils.security import hash_password, verify_password


def _hash_jti(jti: str) -> str:
    """Same rationale as RefreshToken's own docstring: never store the
    raw refresh token or its raw jti, only a hash of it."""
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()


class AuthService:
    # ------------------------------------------------------------------
    # Step 7 -- Registration (UNCHANGED from Phase 2)
    # ------------------------------------------------------------------

    @staticmethod
    def register_business(data: dict) -> Tuple[User, dict]:
        if UserRepository.exists_by_email(data["email"]):
            raise ConflictError("An account with this email already exists.")

        user = UserRepository.create(
            email=data["email"],
            password_hash=hash_password(data["password"]),
            role=UserRole.BUSINESS,
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        tokens = AuthService._issue_tokens(user)
        return user, tokens

    @staticmethod
    def register_supplier(data: dict) -> Tuple[User, dict]:
        if UserRepository.exists_by_email(data["email"]):
            raise ConflictError("An account with this email already exists.")

        user = UserRepository.create(
            email=data["email"],
            password_hash=hash_password(data["password"]),
            role=UserRole.SUPPLIER,
            first_name=data["owner_name"],
            last_name=None,
        )
        tokens = AuthService._issue_tokens(user)
        return user, tokens

    # ------------------------------------------------------------------
    # Step 8 -- Login (UNCHANGED from Phase 2)
    # ------------------------------------------------------------------

    @staticmethod
    def login(email: str, password: str) -> Tuple[User, dict]:
        user = UserRepository.get_by_email(email)

        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise ForbiddenError("This account has been deactivated.")

        UserRepository.update_last_login(user)
        tokens = AuthService._issue_tokens(user)
        return user, tokens

    # ------------------------------------------------------------------
    # Step 9 -- JWT issuance, extended for Step 11 (persistence)
    # ------------------------------------------------------------------

    @staticmethod
    def _issue_tokens(
        user: User, device_id: Optional[str] = None, ip_address: Optional[str] = None
    ) -> dict:
        """Issues an access + refresh token pair. Every refresh token
        issued here also gets a corresponding RefreshToken row (Step 11)
        so it can later be looked up and revoked -- access tokens remain
        fully stateless (Step 12 rule), only refresh tokens are tracked.
        """
        additional_claims = {"role": user.role.value}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)

        jti = get_jti(refresh_token)
        expires_at = utcnow() + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
        RefreshTokenRepository.create(
            user_id=user.id,
            jti_hash=_hash_jti(jti),
            expires_at=expires_at,
            device_id=device_id,
            ip_address=ip_address,
        )

        return {"access_token": access_token, "refresh_token": refresh_token}

    # ------------------------------------------------------------------
    # Step 11 -- Refresh Token rotation
    # ------------------------------------------------------------------

    @staticmethod
    def refresh(current_jti: str, user_id: str, device_id: Optional[str] = None, ip_address: Optional[str] = None) -> dict:
        """Validates the presented refresh token against the database
        (not just its JWT signature/expiry, which flask_jwt_extended
        already checked before this method is called) and ROTATES it:
        the token just used is revoked, and a brand new access+refresh
        pair is issued. This means a refresh token can only ever be used
        once -- if a stolen refresh token is used by an attacker, the
        legitimate user's next refresh attempt will fail (the token was
        already revoked), which is a detectable signal of compromise
        even though this generator doesn't yet build an alerting system
        around that signal.
        """
        token_record = RefreshTokenRepository.get_by_jti_hash(_hash_jti(current_jti))

        if token_record is None or not token_record.is_valid():
            raise UnauthorizedError("Refresh token is invalid or has been revoked.")

        RefreshTokenRepository.revoke(token_record)

        user = UserRepository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found.")

        return AuthService._issue_tokens(user, device_id=device_id, ip_address=ip_address)

    # ------------------------------------------------------------------
    # Step 12 -- Logout
    # ------------------------------------------------------------------

    @staticmethod
    def logout(user_id: str, refresh_token_jti: Optional[str] = None) -> None:
        """Single-device logout when the caller provides the specific
        refresh token's jti (revokes only that one). Falls back to
        revoking EVERY active refresh token for the user when no
        specific jti is provided -- a safe default, and currently the
        path the mobile app actually exercises, since
        frontend/mobile/src/services/auth/authService.ts's logout()
        does not yet send a refresh token in the request body. Update
        that function to POST {"refresh_token": "..."} for true
        single-device semantics; until then this safe fallback is what
        runs.
        """
        if refresh_token_jti:
            token_record = RefreshTokenRepository.get_by_jti_hash(_hash_jti(refresh_token_jti))
            if token_record is not None and str(token_record.user_id) == str(user_id):
                RefreshTokenRepository.revoke(token_record)
            return

        RefreshTokenRepository.revoke_all_for_user(user_id)

    @staticmethod
    def get_current_user(user_id: str) -> User:
        user = UserRepository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found.")
        return user
'''


# ==============================================================================
# Step 13 -- OTP Service
# ==============================================================================

FILES[os.path.join("src", "services", "otp_service.py")] = r'''"""
OTP Verification Service.
Ref: continuation master prompt (Phase 3), Step 13.

DESIGN NOTE -- why this verifies by EMAIL, not phone, for now:
frontend/mobile's registration screens (per an explicit later
simplification of the original design) no longer collect a phone number
at registration -- phone number is only collected later, in the Business
Profile Setup wizard (Step 2: Owner Information). At the point the
mobile app's Verify-OTP screen actually runs (immediately after
registration, before profile setup), the only destination available is
the user's email. This service therefore defaults to
OTPPurpose.EMAIL_VERIFICATION and resolves the user by looking up their
email -- OTPPurpose.PHONE_VERIFICATION is fully implemented and ready to
use once a phone-based verification step is wired up after profile setup
collects a phone number, but nothing calls it that way yet.

Also deliberately NOT behind @jwt_required() (see src/api/auth_routes.py)
-- the user does not yet have a stored access token at this point in the
mobile flow (useRegister's onSuccess navigates straight to the OTP screen
without persisting tokens; only useSignIn/useGoogleSignIn currently
store tokens). Requests are authorized by knowing the destination
(email) instead, matching frontend/mobile's VerifyOtpPayload shape
({destination, code}, no auth header).
"""
from __future__ import annotations

from datetime import timedelta

from flask import current_app

from src.core.base_model import utcnow
from src.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from src.extensions import db
from src.models.otp_verification import OTPPurpose
from src.models.user import VerificationStatus
from src.repositories.otp_repository import OTPRepository
from src.repositories.user_repository import UserRepository
from src.utils.otp import generate_numeric_otp, hash_otp, verify_otp_hash

OTP_EXPIRY_MINUTES = 10


class OTPService:
    @staticmethod
    def request_otp(destination: str, purpose: OTPPurpose = OTPPurpose.EMAIL_VERIFICATION) -> None:
        user = UserRepository.get_by_email(destination)
        if user is None:
            # Same principle as forgot-password: do not reveal whether
            # this destination is associated with an account.
            return

        code = generate_numeric_otp()
        expires_at = utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        OTPRepository.create(
            user_id=user.id,
            purpose=purpose,
            destination=destination,
            otp_code_hash=hash_otp(code),
            expires_at=expires_at,
        )

        # Future SMS/WhatsApp/email-provider integration point (Step 13:
        # "Prepare for future providers without redesign"). No real
        # provider is wired in yet -- logged so the code is usable during
        # development instead of silently vanishing.
        current_app.logger.info(
            "OTP for %s (%s): %s [DEV ONLY -- wire up a real provider before production]",
            destination,
            purpose.value,
            code,
        )

    @staticmethod
    def verify_otp(destination: str, code: str, purpose: OTPPurpose = OTPPurpose.EMAIL_VERIFICATION) -> None:
        user = UserRepository.get_by_email(destination)
        if user is None:
            raise NotFoundError("No account found for this destination.")

        record = OTPRepository.get_latest_active(user.id, purpose)
        if record is None:
            raise UnauthorizedError("No pending verification code found. Please request a new one.")

        if record.is_expired():
            raise UnauthorizedError("This verification code has expired. Please request a new one.")

        if not record.has_attempts_remaining():
            raise ForbiddenError("Too many incorrect attempts. Please request a new verification code.")

        if record.destination != destination or not verify_otp_hash(code, record.otp_code_hash):
            OTPRepository.increment_attempts(record)
            raise UnauthorizedError("Incorrect verification code.")

        OTPRepository.mark_used(record)

        user.verification_status = VerificationStatus.VERIFIED
        db.session.commit()
'''


# ==============================================================================
# Step 14 -- Password Reset Service
# ==============================================================================

FILES[os.path.join("src", "services", "password_reset_service.py")] = r'''"""
Forgot/Reset Password Service.
Ref: continuation master prompt (Phase 3), Step 14.
"""
from __future__ import annotations

from datetime import timedelta

from flask import current_app

from src.core.base_model import utcnow
from src.core.exceptions import UnauthorizedError
from src.extensions import db
from src.repositories.password_reset_repository import PasswordResetRepository
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.repositories.user_repository import UserRepository
from src.utils.otp import generate_reset_token, hash_reset_token
from src.utils.security import hash_password

RESET_TOKEN_EXPIRY_HOURS = 1


class PasswordResetService:
    @staticmethod
    def forgot_password(email: str) -> None:
        """Step 14 rule: "Never expose whether an email exists" -- this
        method behaves identically (returns None, no exception) whether
        or not a matching user was found. Callers must never branch on
        this method's result to decide what to tell the client."""
        user = UserRepository.get_by_email(email)
        if user is None:
            return

        raw_token = generate_reset_token()
        expires_at = utcnow() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)
        PasswordResetRepository.create(
            user_id=user.id, token_hash=hash_reset_token(raw_token), expires_at=expires_at
        )

        # Future email-service integration point (Step 14: "Prepare
        # architecture for future email service integration"). No real
        # provider wired in yet -- logged for development usability.
        current_app.logger.info(
            "Password reset token for %s: %s [DEV ONLY -- wire up a real email provider before production]",
            email,
            raw_token,
        )

    @staticmethod
    def reset_password(token: str, new_password: str) -> None:
        record = PasswordResetRepository.get_by_token_hash(hash_reset_token(token))

        if record is None or not record.is_valid():
            raise UnauthorizedError("This password reset link is invalid or has expired.")

        user = UserRepository.get_by_id(record.user_id)
        if user is None:
            raise UnauthorizedError("This password reset link is invalid or has expired.")

        user.password_hash = hash_password(new_password)
        db.session.commit()

        PasswordResetRepository.mark_used(record)

        # Step 14 rule: "Password reset must invalidate previous
        # credentials where appropriate" -- force re-login on every
        # device by revoking all of this user's active refresh tokens.
        RefreshTokenRepository.revoke_all_for_user(user.id)
'''

# ==============================================================================
# Step 15 -- Role Authorization, extended with a permission_required stub
# ==============================================================================
# role_required is UNCHANGED from Phase 2. permission_required is new --
# a structural placeholder for granular permissions (Step 15: "Future
# granular permissions"), since no Permission/RolePermission model exists
# yet. It currently checks a "permissions" JWT claim if present (which
# nothing populates yet) and is documented clearly as a placeholder
# rather than a real permission system, so nobody mistakes it for one.

FILES[os.path.join("src", "core", "decorators.py")] = r'''"""
Authorization decorators.
Ref: continuation master prompt, Step 10 (role_required) and Step 15
(permission_required) -- "Authorization must remain independent from
authentication... Create reusable decorators... Support Role validation,
Permission validation, Future granular permissions."
"""
from __future__ import annotations

from functools import wraps

from flask_jwt_extended import get_jwt, jwt_required

from src.core.exceptions import ForbiddenError


def role_required(*allowed_roles: str):
    """Stacks JWT verification + role authorization in one decorator.

        @some_bp.get("/business-only-thing")
        @role_required("business")
        def business_only_thing():
            ...

    Multiple roles may be passed (e.g. @role_required("business", "admin")).
    Supports every role in UserRole (business, supplier, admin) and any
    future role added to that enum without this decorator changing.
    """

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                raise ForbiddenError("You do not have permission to access this resource.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def permission_required(*required_permissions: str):
    """STRUCTURAL PLACEHOLDER for granular, permission-level
    authorization (Step 15: "Future granular permissions"). No
    Permission/RolePermission model exists yet -- there is nowhere to
    look up what permissions a role actually grants. This decorator
    checks for a "permissions" JWT claim, which nothing currently
    populates, so as written it will deny access to everything until:

      1. A Permission model + role-to-permission mapping is built, and
      2. AuthService._issue_tokens is updated to include a resolved
         "permissions" list in additional_claims.

    Included now so route signatures that will eventually need
    permission checks (rather than just role checks) can be written
    against this decorator today, without every call site needing to
    change later -- only this function's internals do.
    """

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            granted = set(claims.get("permissions", []))
            if not set(required_permissions).issubset(granted):
                raise ForbiddenError("You do not have permission to access this resource.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
'''


# ==============================================================================
# Steps 7-14 -- Routes, REWRITTEN. Register/login/me are UNCHANGED from
# Phase 2. refresh/logout are extended. OTP + forgot/reset-password are
# new.
# ==============================================================================

FILES[os.path.join("src", "api", "auth_routes.py")] = r'''"""
Authentication Routes.
Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1; continuation
master prompt, Steps 7-14.

Routes ONLY: validate the request (via Marshmallow), call the service
layer, return the standard response envelope. No business logic and no
direct SQLAlchemy access here.
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jti, get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.responses import error_response, success_response
from src.schemas.auth_schemas import BusinessRegisterSchema, LoginSchema, SupplierRegisterSchema
from src.schemas.otp_schemas import RequestOtpSchema, VerifyOtpSchema
from src.schemas.password_reset_schemas import ForgotPasswordSchema, ResetPasswordSchema
from src.services.auth_service import AuthService
from src.services.otp_service import OTPService
from src.services.password_reset_service import PasswordResetService

auth_bp = Blueprint("auth", __name__)

_business_register_schema = BusinessRegisterSchema()
_supplier_register_schema = SupplierRegisterSchema()
_login_schema = LoginSchema()
_request_otp_schema = RequestOtpSchema()
_verify_otp_schema = VerifyOtpSchema()
_forgot_password_schema = ForgotPasswordSchema()
_reset_password_schema = ResetPasswordSchema()


def _flatten_errors(messages) -> list:
    flat: list = []
    if isinstance(messages, dict):
        for field, field_errors in messages.items():
            if isinstance(field_errors, list):
                for msg in field_errors:
                    flat.append(f"{field}: {msg}")
            else:
                flat.append(f"{field}: {field_errors}")
    elif isinstance(messages, list):
        flat.extend(str(m) for m in messages)
    return flat


# ------------------------------------------------------------------------
# Steps 7-8 -- Registration & Login (UNCHANGED from Phase 2)
# ------------------------------------------------------------------------

@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    role = payload.get("role")

    if role == "business":
        schema = _business_register_schema
    elif role == "supplier":
        schema = _supplier_register_schema
    else:
        return error_response(
            message="Validation failed", errors=["role: must be 'business' or 'supplier'"], status_code=422
        )

    try:
        data = schema.load({k: v for k, v in payload.items() if k != "role"})
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    if role == "business":
        user, tokens = AuthService.register_business(data)
        message = "Business account created successfully."
    else:
        user, tokens = AuthService.register_supplier(data)
        message = "Supplier account created successfully."

    return success_response(
        data={"user": user.to_public_dict(), "tokens": tokens}, message=message, status_code=201
    )


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    try:
        data = _login_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    user, tokens = AuthService.login(data["email"], data["password"])
    return success_response(data={"user": user.to_public_dict(), "tokens": tokens}, message="Login successful.")


# ------------------------------------------------------------------------
# Step 11 -- Refresh Token rotation
# ------------------------------------------------------------------------

@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """Rotation: returns a NEW access_token AND a NEW refresh_token; the
    refresh token that authenticated this request is revoked as part of
    AuthService.refresh(). The mobile app does not yet call this
    endpoint (frontend/mobile's apiClient.ts has a comment noting 401
    refresh-exchange handling is not wired up yet) -- when it is, it
    must store BOTH returned tokens, not just the access token, since
    the old refresh token stops working after this call."""
    identity = get_jwt_identity()
    claims = get_jwt()
    tokens = AuthService.refresh(current_jti=claims.get("jti"), user_id=identity)
    return success_response(data=tokens, message="Token refreshed.")


# ------------------------------------------------------------------------
# Step 10 -- Current user
# ------------------------------------------------------------------------

@auth_bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()
    user = AuthService.get_current_user(identity)
    return success_response(data=user.to_public_dict())


# ------------------------------------------------------------------------
# Step 12 -- Logout
# ------------------------------------------------------------------------

@auth_bp.post("/logout")
@jwt_required(verify_type=False)
def logout():
    """Authenticated with the caller's ACCESS token (matching what
    frontend/mobile's authService.logout() already sends). Optionally
    accepts {"refresh_token": "..."} in the body for true single-device
    revocation -- the mobile client does not send this yet, so today
    this always falls back to AuthService.logout()'s safe default
    (revoke every active refresh token for the user). See that method's
    docstring for the full rationale."""
    identity = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    raw_refresh_token = payload.get("refresh_token")

    refresh_token_jti = None
    if raw_refresh_token:
        try:
            refresh_token_jti = get_jti(raw_refresh_token)
        except Exception:  # noqa: BLE001 - any decode failure just means "no usable jti"
            refresh_token_jti = None

    AuthService.logout(user_id=identity, refresh_token_jti=refresh_token_jti)
    return success_response(message="Logged out.")


# ------------------------------------------------------------------------
# Step 13 -- OTP Verification (see src/services/otp_service.py docstring
# for why this verifies by email, not phone, given the current mobile
# registration flow)
# ------------------------------------------------------------------------

@auth_bp.post("/phone/request-otp")
def request_otp():
    payload = request.get_json(silent=True) or {}
    try:
        data = _request_otp_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    OTPService.request_otp(destination=data["destination"])
    return success_response(message="If an account exists for this destination, a verification code has been sent.")


@auth_bp.post("/phone/verify-otp")
def verify_otp():
    payload = request.get_json(silent=True) or {}
    try:
        data = _verify_otp_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    OTPService.verify_otp(destination=data["destination"], code=data["code"])
    return success_response(message="Verification successful.")


# ------------------------------------------------------------------------
# Step 14 -- Forgot / Reset Password
# ------------------------------------------------------------------------

@auth_bp.post("/forgot-password")
def forgot_password():
    payload = request.get_json(silent=True) or {}
    try:
        data = _forgot_password_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    PasswordResetService.forgot_password(data["email"])
    return success_response(
        message="If an account exists for this email, password reset instructions have been sent."
    )


@auth_bp.post("/reset-password")
def reset_password():
    payload = request.get_json(silent=True) or {}
    try:
        data = _reset_password_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    PasswordResetService.reset_password(token=data["token"], new_password=data["new_password"])
    return success_response(message="Password has been reset successfully.")
'''

# ==============================================================================
# Step 16 -- Authentication Test Suite, EXTENDED
# Steps 5-10 tests (password security, register/login schemas, register/
# login/me integration) are UNCHANGED from Phase 2. Steps 11-15 coverage
# is new: refresh rotation, logout revocation, OTP (happy path, expiry,
# attempt-limiting, reuse), forgot/reset password (enumeration
# protection, token replay, refresh-token invalidation), and role_required
# authorization.
# ==============================================================================

FILES[os.path.join("tests", "test_auth.py")] = r'''"""
Authentication module tests.
Ref: continuation master prompt, Step 16 (Authentication Test Suite).

Two groups, as in Phase 2:
1. Pure unit tests -- no database connection needed. Run anywhere:
       pytest tests/test_auth.py -k "not Integration"
2. Integration tests -- need a real PostgreSQL test database
   (TestingConfig -> tru_connect_test, see src/config.py):
       pytest tests/test_auth.py -k Integration
"""
from __future__ import annotations

import time

import pytest

from src import create_app
from src.extensions import db
from src.schemas.auth_schemas import BusinessRegisterSchema, LoginSchema, SupplierRegisterSchema
from src.schemas.otp_schemas import RequestOtpSchema, VerifyOtpSchema
from src.schemas.password_reset_schemas import ForgotPasswordSchema, ResetPasswordSchema
from src.utils.otp import generate_numeric_otp, generate_reset_token, hash_otp, hash_reset_token, verify_otp_hash
from src.utils.security import hash_password, passwords_match, validate_password_complexity, verify_password


# ----------------------------------------------------------------------------
# Group 1: pure unit tests -- no database required.
# ----------------------------------------------------------------------------

class TestPasswordSecurity:
    def test_hash_and_verify_round_trip(self):
        hashed = hash_password("correct horse battery staple 1")
        assert verify_password("correct horse battery staple 1", hashed)

    def test_verify_rejects_wrong_password(self):
        hashed = hash_password("correct horse battery staple 1")
        assert not verify_password("wrong password", hashed)

    def test_complexity_rejects_short_password(self):
        assert any("8 characters" in e for e in validate_password_complexity("ab1"))

    def test_complexity_rejects_no_digit(self):
        assert any("number" in e for e in validate_password_complexity("abcdefgh"))

    def test_complexity_rejects_no_letter(self):
        assert any("letter" in e for e in validate_password_complexity("12345678"))

    def test_complexity_accepts_valid_password(self):
        assert validate_password_complexity("abcd1234") == []

    def test_passwords_match(self):
        assert passwords_match("abcd1234", "abcd1234")
        assert not passwords_match("abcd1234", "different1")


class TestOtpUtilities:
    def test_generated_otp_is_correct_length_and_numeric(self):
        code = generate_numeric_otp()
        assert len(code) == 6
        assert code.isdigit()

    def test_otp_hash_round_trip(self):
        code = generate_numeric_otp()
        assert verify_otp_hash(code, hash_otp(code))

    def test_otp_hash_rejects_wrong_code(self):
        code_hash = hash_otp("123456")
        assert not verify_otp_hash("654321", code_hash)

    def test_reset_token_is_url_safe_and_reasonably_long(self):
        token = generate_reset_token()
        assert len(token) >= 32

    def test_reset_token_hash_is_deterministic(self):
        token = generate_reset_token()
        assert hash_reset_token(token) == hash_reset_token(token)


class TestBusinessRegisterSchema:
    def _valid_payload(self, **overrides):
        payload = {
            "firstName": "Thabo",
            "lastName": "Nkosi",
            "email": "thabo@example.com",
            "password": "abcd1234",
            "confirmPassword": "abcd1234",
            "acceptPrivacyPolicy": True,
        }
        payload.update(overrides)
        return payload

    def test_accepts_valid_camel_case_payload(self):
        data = BusinessRegisterSchema().load(self._valid_payload())
        assert data["first_name"] == "Thabo"

    def test_rejects_mismatched_passwords(self):
        with pytest.raises(Exception):
            BusinessRegisterSchema().load(self._valid_payload(confirmPassword="different1"))

    def test_rejects_missing_privacy_policy_acceptance(self):
        with pytest.raises(Exception):
            BusinessRegisterSchema().load(self._valid_payload(acceptPrivacyPolicy=False))


class TestSupplierRegisterSchema:
    def test_accepts_valid_payload(self):
        data = SupplierRegisterSchema().load(
            {
                "ownerName": "Naledi Dlamini",
                "email": "naledi@example.com",
                "password": "abcd1234",
                "confirmPassword": "abcd1234",
                "acceptTerms": True,
            }
        )
        assert data["owner_name"] == "Naledi Dlamini"


class TestLoginSchema:
    def test_accepts_valid_payload(self):
        data = LoginSchema().load({"email": "a@example.com", "password": "abcd1234"})
        assert data["email"] == "a@example.com"


class TestOtpSchemas:
    def test_request_otp_schema_valid(self):
        data = RequestOtpSchema().load({"destination": "test@example.com"})
        assert data["destination"] == "test@example.com"

    def test_verify_otp_schema_rejects_wrong_length_code(self):
        with pytest.raises(Exception):
            VerifyOtpSchema().load({"destination": "test@example.com", "code": "123"})

    def test_verify_otp_schema_accepts_six_digit_code(self):
        data = VerifyOtpSchema().load({"destination": "test@example.com", "code": "123456"})
        assert data["code"] == "123456"


class TestPasswordResetSchemas:
    def test_forgot_password_schema_requires_valid_email(self):
        with pytest.raises(Exception):
            ForgotPasswordSchema().load({"email": "not-an-email"})

    def test_reset_password_schema_rejects_mismatched_passwords(self):
        with pytest.raises(Exception):
            ResetPasswordSchema().load(
                {"token": "abc", "newPassword": "abcd1234", "confirmPassword": "different1"}
            )

    def test_reset_password_schema_rejects_weak_password(self):
        with pytest.raises(Exception):
            ResetPasswordSchema().load({"token": "abc", "newPassword": "weak", "confirmPassword": "weak"})

    def test_reset_password_schema_accepts_valid_payload(self):
        data = ResetPasswordSchema().load(
            {"token": "abc", "newPassword": "abcd1234", "confirmPassword": "abcd1234"}
        )
        assert data["new_password"] == "abcd1234"


# ----------------------------------------------------------------------------
# Group 2: integration tests -- require a real PostgreSQL test database.
# ----------------------------------------------------------------------------

@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _register_business(client, email="thabo@example.com"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "role": "business",
            "firstName": "Thabo",
            "lastName": "Nkosi",
            "email": email,
            "password": "abcd1234",
            "confirmPassword": "abcd1234",
            "acceptPrivacyPolicy": True,
        },
    )


class TestRegistrationIntegration:
    def test_register_business_returns_tokens(self, client):
        response = _register_business(client)
        assert response.status_code == 201
        body = response.get_json()
        assert "access_token" in body["data"]["tokens"]
        assert "refresh_token" in body["data"]["tokens"]
        assert "password_hash" not in body["data"]["user"]

    def test_duplicate_email_is_rejected(self, client):
        _register_business(client, email="dup@example.com")
        second = _register_business(client, email="dup@example.com")
        assert second.status_code == 409


class TestLoginIntegration:
    def test_login_with_correct_credentials(self, client):
        _register_business(client, email="login-test@example.com")
        response = client.post(
            "/api/v1/auth/login", json={"email": "login-test@example.com", "password": "abcd1234"}
        )
        assert response.status_code == 200

    def test_login_with_wrong_password_returns_401(self, client):
        _register_business(client, email="wrongpass@example.com")
        response = client.post(
            "/api/v1/auth/login", json={"email": "wrongpass@example.com", "password": "wrong9999"}
        )
        assert response.status_code == 401


class TestProtectedRoutesIntegration:
    def test_me_requires_authentication(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_me_returns_current_user_with_valid_token(self, client):
        register_response = _register_business(client, email="me-test@example.com")
        access_token = register_response.get_json()["data"]["tokens"]["access_token"]
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200
        assert response.get_json()["data"]["email"] == "me-test@example.com"


class TestRefreshTokenIntegration:
    def test_refresh_returns_new_token_pair(self, client):
        register_response = _register_business(client, email="refresh-test@example.com")
        original_refresh = register_response.get_json()["data"]["tokens"]["refresh_token"]

        response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {original_refresh}"}
        )
        assert response.status_code == 200
        body = response.get_json()["data"]
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["refresh_token"] != original_refresh

    def test_rotated_refresh_token_cannot_be_reused(self, client):
        """Core of Step 11's rotation requirement: once a refresh token
        has been used to get a new pair, using the SAME old token again
        must fail."""
        register_response = _register_business(client, email="rotation-test@example.com")
        original_refresh = register_response.get_json()["data"]["tokens"]["refresh_token"]

        first_use = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {original_refresh}"}
        )
        assert first_use.status_code == 200

        second_use = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {original_refresh}"}
        )
        assert second_use.status_code == 401

    def test_access_token_cannot_be_used_to_refresh(self, client):
        register_response = _register_business(client, email="wrongtype-test@example.com")
        access_token = register_response.get_json()["data"]["tokens"]["access_token"]

        response = client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 422  # flask-jwt-extended rejects wrong token type


class TestLogoutIntegration:
    def test_logout_revokes_refresh_token(self, client):
        """Mobile client's current behaviour: POST /auth/logout with only
        an access token, no refresh_token in the body -- AuthService
        falls back to revoking ALL of the user's refresh tokens."""
        register_response = _register_business(client, email="logout-test@example.com")
        tokens = register_response.get_json()["data"]["tokens"]

        logout_response = client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert logout_response.status_code == 200

        refresh_response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
        )
        assert refresh_response.status_code == 401

    def test_logout_with_explicit_refresh_token_revokes_only_that_one(self, client):
        register_response = _register_business(client, email="explicit-logout@example.com")
        tokens = register_response.get_json()["data"]["tokens"]

        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert logout_response.status_code == 200

        refresh_response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
        )
        assert refresh_response.status_code == 401


class TestOtpIntegration:
    def _get_logged_otp(self, caplog, email):
        """The dev-mode OTP delivery logs the code via app.logger.info
        (see OTPService docstring) -- tests parse it out of the captured
        log rather than needing a real SMS/email provider."""
        import re

        for record in caplog.records:
            if email in record.message:
                match = re.search(r": (\d{6}) ", record.message + " ")
                if match:
                    return match.group(1)
        return None

    def test_request_then_verify_otp_succeeds(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="otp-test@example.com")

        request_response = client.post(
            "/api/v1/auth/phone/request-otp", json={"destination": "otp-test@example.com"}
        )
        assert request_response.status_code == 200

        code = self._get_logged_otp(caplog, "otp-test@example.com")
        assert code is not None

        verify_response = client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "otp-test@example.com", "code": code}
        )
        assert verify_response.status_code == 200

    def test_wrong_otp_code_is_rejected(self, client):
        _register_business(client, email="otp-wrong@example.com")
        client.post("/api/v1/auth/phone/request-otp", json={"destination": "otp-wrong@example.com"})

        response = client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "otp-wrong@example.com", "code": "000000"}
        )
        assert response.status_code == 401

    def test_otp_cannot_be_reused_after_success(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="otp-reuse@example.com")
        client.post("/api/v1/auth/phone/request-otp", json={"destination": "otp-reuse@example.com"})
        code = self._get_logged_otp(caplog, "otp-reuse@example.com")

        first = client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "otp-reuse@example.com", "code": code}
        )
        assert first.status_code == 200

        second = client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "otp-reuse@example.com", "code": code}
        )
        assert second.status_code == 401

    def test_otp_locks_out_after_too_many_wrong_attempts(self, client):
        _register_business(client, email="otp-lockout@example.com")
        client.post("/api/v1/auth/phone/request-otp", json={"destination": "otp-lockout@example.com"})

        last_response = None
        for _ in range(6):  # max_attempts defaults to 5
            last_response = client.post(
                "/api/v1/auth/phone/verify-otp",
                json={"destination": "otp-lockout@example.com", "code": "000000"},
            )
        assert last_response.status_code == 403

    def test_request_otp_for_unknown_destination_does_not_error(self, client):
        """Enumeration protection: requesting an OTP for a destination
        with no matching account must not reveal that fact via a
        different status code."""
        response = client.post(
            "/api/v1/auth/phone/request-otp", json={"destination": "nobody@example.com"}
        )
        assert response.status_code == 200


class TestPasswordResetIntegration:
    def _get_logged_token(self, caplog, email):
        for record in caplog.records:
            if email in record.message and "Password reset token" in record.message:
                parts = record.message.split(": ")
                return parts[1].split(" ")[0] if len(parts) > 1 else None
        return None

    def test_forgot_password_returns_same_message_for_known_and_unknown_email(self, client):
        known = _register_business(client, email="forgot-known@example.com")
        assert known.status_code == 201

        known_response = client.post("/api/v1/auth/forgot-password", json={"email": "forgot-known@example.com"})
        unknown_response = client.post("/api/v1/auth/forgot-password", json={"email": "forgot-unknown@example.com"})

        assert known_response.status_code == unknown_response.status_code == 200
        assert known_response.get_json()["message"] == unknown_response.get_json()["message"]

    def test_reset_password_with_valid_token_changes_password(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="reset-flow@example.com")
        client.post("/api/v1/auth/forgot-password", json={"email": "reset-flow@example.com"})
        token = self._get_logged_token(caplog, "reset-flow@example.com")
        assert token is not None

        reset_response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "newPassword": "newpass123", "confirmPassword": "newpass123"},
        )
        assert reset_response.status_code == 200

        old_password_login = client.post(
            "/api/v1/auth/login", json={"email": "reset-flow@example.com", "password": "abcd1234"}
        )
        assert old_password_login.status_code == 401

        new_password_login = client.post(
            "/api/v1/auth/login", json={"email": "reset-flow@example.com", "password": "newpass123"}
        )
        assert new_password_login.status_code == 200

    def test_reset_token_cannot_be_reused(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="reset-replay@example.com")
        client.post("/api/v1/auth/forgot-password", json={"email": "reset-replay@example.com"})
        token = self._get_logged_token(caplog, "reset-replay@example.com")

        first = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "newPassword": "newpass123", "confirmPassword": "newpass123"},
        )
        assert first.status_code == 200

        second = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "newPassword": "anotherpass1", "confirmPassword": "anotherpass1"},
        )
        assert second.status_code == 401

    def test_reset_password_invalidates_existing_refresh_tokens(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        register_response = _register_business(client, email="reset-revokes@example.com")
        original_refresh = register_response.get_json()["data"]["tokens"]["refresh_token"]

        client.post("/api/v1/auth/forgot-password", json={"email": "reset-revokes@example.com"})
        token = self._get_logged_token(caplog, "reset-revokes@example.com")
        client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "newPassword": "newpass123", "confirmPassword": "newpass123"},
        )

        refresh_response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {original_refresh}"}
        )
        assert refresh_response.status_code == 401


class TestRoleAuthorizationIntegration:
    def test_role_required_allows_matching_role(self, app, client):
        from flask import jsonify

        from src.core.decorators import role_required

        @app.route("/api/v1/_test/business-only")
        @role_required("business")
        def _business_only():
            return jsonify({"ok": True})

        register_response = _register_business(client, email="role-test@example.com")
        access_token = register_response.get_json()["data"]["tokens"]["access_token"]

        response = client.get(
            "/api/v1/_test/business-only", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200

    def test_role_required_blocks_non_matching_role(self, app, client):
        from flask import jsonify

        from src.core.decorators import role_required

        @app.route("/api/v1/_test/supplier-only")
        @role_required("supplier")
        def _supplier_only():
            return jsonify({"ok": True})

        register_response = _register_business(client, email="role-block-test@example.com")
        access_token = register_response.get_json()["data"]["tokens"]["access_token"]

        response = client.get(
            "/api/v1/_test/supplier-only", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 403
'''


# ==============================================================================
# INTEGRATION -- targeted edit to src/models/__init__.py, adding the 3
# new Phase 3 models to the import already added in Phase 2.
# ==============================================================================

def integrate_models_init_phase3(backend_dir: str) -> str:
    path = os.path.join(backend_dir, "src", "models", "__init__.py")
    if not os.path.isfile(path):
        return "skipped"

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    import_line = (
        "from src.models.refresh_token import RefreshToken\n"
        "from src.models.otp_verification import OTPPurpose, OTPVerification\n"
        "from src.models.password_reset_token import PasswordResetToken\n"
    )

    if "from src.models.refresh_token import" in content:
        return "already-integrated"

    new_content = content.rstrip("\n") + "\n\n" + import_line
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return "integrated"


# ==============================================================================
# GENERATION LOGIC
# ==============================================================================

def print_plan(backend_dir: str) -> None:
    print("=" * 78)
    print(" TRU CONNECT BACKEND - Authentication Module Phase 3 (Steps 11-16)")
    print("=" * 78)
    print(f" Target: {os.path.abspath(backend_dir)}")
    print()
    print(" WRITE (new files):")
    for rel_path in FILES:
        if rel_path not in (
            os.path.join("src", "services", "auth_service.py"),
            os.path.join("src", "core", "decorators.py"),
            os.path.join("src", "api", "auth_routes.py"),
            os.path.join("tests", "test_auth.py"),
        ):
            print(f"   - {rel_path}")
    print()
    print(" REWRITE (existing Steps 7-10 files, extended for Steps 11-16 --")
    print(" register/login business logic and role_required are unchanged,")
    print(" see this script's own docstring for exactly what's new):")
    print("   - src/services/auth_service.py")
    print("   - src/core/decorators.py")
    print("   - src/api/auth_routes.py")
    print("   - tests/test_auth.py")
    print()
    print(" INTEGRATE (targeted edit):")
    print("   - src/models/__init__.py  (imports the 3 new Phase 3 models)")
    print()
    print(" NEVER TOUCHED: src/config.py, src/extensions.py, src/__init__.py,")
    print(" app.py, src/core/base_model.py, src/core/exceptions.py,")
    print(" src/core/responses.py, src/models/user.py,")
    print(" src/repositories/user_repository.py, src/schemas/auth_schemas.py,")
    print(" src/utils/security.py, requirements.txt, .env, migrations/**,")
    print(" docs/**, frontend/**")
    print("=" * 78)


def generate(backend_dir: str) -> None:
    written = 0
    for rel_path, content in FILES.items():
        full_path = os.path.join(backend_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        written += 1
    print(f"   {written} file(s) written.")

    status = integrate_models_init_phase3(backend_dir)
    labels = {
        "integrated": "integrated",
        "already-integrated": "already integrated, no change needed",
        "skipped": "SKIPPED (src/models/__init__.py not found -- run the Phase 2 script first)",
    }
    print(f"   src/models/__init__.py: {labels[status]}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate the TRU Connect backend authentication module, "
        "Phase 3 (Steps 11-16: Refresh Token Management, Logout, OTP "
        "Verification, Forgot Password, Role Authorization, Test Suite)."
    )
    parser.add_argument(
        "--root", default=".", help="Path to the TRU_Connect monorepo root (default: current directory)."
    )
    parser.add_argument("-f", "--force", action="store_true", help="Skip the confirmation prompt.")
    args = parser.parse_args()

    backend_dir = os.path.join(args.root, BACKEND_REL)

    if not os.path.isdir(backend_dir):
        print(f"ERROR: '{backend_dir}' does not exist. Run this from the TRU_Connect root, "
              "or pass --root /path/to/TRU_Connect.")
        sys.exit(1)

    if not os.path.isfile(os.path.join(backend_dir, "src", "services", "auth_service.py")):
        print("ERROR: backend/src/services/auth_service.py not found. Run the Phase 2 "
              "script (Steps 5-10) first.")
        sys.exit(1)

    print_plan(backend_dir)

    if not args.force:
        response = input("Proceed? [y/N]: ")
        if response.strip().lower() != "y":
            print("Aborted. Re-run with --force to skip this prompt next time.")
            sys.exit(1)

    print()
    print("Applying changes...")
    generate(backend_dir)

    print()
    print("=" * 78)
    print(" Done -- Steps 11-16 complete. Full Authentication Module finished.")
    print("=" * 78)
    print(" Next:")
    print(f"   cd {backend_dir}")
    print('   flask db migrate -m "add refresh tokens, otp, password reset tables"')
    print("   flask db upgrade")
    print()
    print(" TESTING (tests/test_auth.py, now covering Steps 5-16):")
    print("   pytest tests/test_auth.py -k \"not Integration\"   # no DB needed")
    print("   pytest tests/test_auth.py -k Integration           # needs real Postgres")
    print()
    print(" Authentication Module complete (Steps 1-16). Awaiting your review")
    print(" before any further backend domains (Business/Supplier profiles, etc.)")
    print(" begin.")
    print("=" * 78)


if __name__ == "__main__":
    main()