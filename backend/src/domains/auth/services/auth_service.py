"""
Authentication Service.
Ref: continuation master prompt, Steps 7-12; "Shared Notification
Infrastructure" master prompt (welcome email -- now sent from
OTPService, not here); Auth Hardening master prompt, Objectives 1-2-9.

REGISTRATION NO LONGER ISSUES TOKENS
-------------------------------------
register_business/register_supplier create the account and send the
verification OTP -- nothing else. There is no token to bypass with,
because none is issued until OTPService.verify_otp succeeds. Verifying
email IS the first authenticated moment for a new account.

UNVERIFIED RE-REGISTRATION POLICY
-----------------------------------
  - Existing account is VERIFIED             -> 409 Conflict (blocks).
  - Existing account is UNVERIFIED and past
    UNVERIFIED_ACCOUNT_EXPIRY_HOURS           -> hard-deleted; treated as
                                                  if it never existed;
                                                  fresh registration
                                                  proceeds normally.
  - Existing account is UNVERIFIED, within
    the window, SAME role requested           -> "resumed": profile
                                                  fields updated, a new
                                                  OTP is sent. This is
                                                  NOT a duplicate account
                                                  -- same row.
  - Existing account is UNVERIFIED, within
    the window, DIFFERENT role requested       -> 409 Conflict. Silently
                                                  flipping an unverified
                                                  account's role on every
                                                  registration attempt
                                                  was the exact bypass
                                                  pattern found in
                                                  testing; this closes it.

LOGIN GATING
-------------
Login enforces, in order: failed-attempt lockout, credential check,
account_status == ACTIVE, verification_status == VERIFIED. Only after
all four pass are tokens issued. See login() below for the exact
structured error each failure mode returns.
"""
from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from flask import current_app

from flask_jwt_extended import create_access_token, create_refresh_token, get_jti

from src.core.base_model import utcnow
from src.core.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    ConflictError,
    EmailNotVerifiedError,
    UnauthorizedError,
)
from src.domains.auth.models.user import AccountStatus, User, UserRole, VerificationStatus
from src.domains.auth.repositories.refresh_token_repository import RefreshTokenRepository
from src.domains.auth.repositories.user_repository import UserRepository
from src.shared import audit
from src.shared.cache import cache
from src.shared.constants import (
    DEFAULT_LOGIN_LOCKOUT_WINDOW_MINUTES,
    DEFAULT_LOGIN_MAX_FAILED_ATTEMPTS,
    DEFAULT_UNVERIFIED_ACCOUNT_EXPIRY_HOURS,
)
from src.shared.security import hash_password, verify_password


def _hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()


def _login_lockout_key(email: str) -> str:
    return f"login_failed:{email.strip().lower()}"


class AuthService:
    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    @staticmethod
    def register_business(data: dict) -> User:
        user = AuthService._create_or_resume(
            data=data, role=UserRole.BUSINESS, first_name=data["first_name"], last_name=data["last_name"]
        )
        AuthService._send_verification_otp(user)
        return user

    @staticmethod
    def register_supplier(data: dict) -> User:
        user = AuthService._create_or_resume(
            data=data, role=UserRole.SUPPLIER, first_name=data["owner_name"], last_name=None
        )
        AuthService._send_verification_otp(user)
        return user

    @staticmethod
    def _is_unverified_expired(user: User) -> bool:
        expiry_hours = current_app.config.get(
            "UNVERIFIED_ACCOUNT_EXPIRY_HOURS", DEFAULT_UNVERIFIED_ACCOUNT_EXPIRY_HOURS
        )
        return (utcnow() - user.created_at).total_seconds() > expiry_hours * 3600

    @staticmethod
    def _create_or_resume(data: dict, role: UserRole, first_name: str, last_name: Optional[str]) -> User:
        existing = UserRepository.get_by_email(data["email"])

        if existing is not None:
            if existing.verification_status == VerificationStatus.VERIFIED:
                raise ConflictError("An account with this email already exists.")

            if AuthService._is_unverified_expired(existing):
                audit.log_unverified_account_expired(existing.email)
                UserRepository.hard_delete(existing)
                existing = None
            elif existing.role != role:
                audit.log_registration_role_conflict(data["email"], existing.role.value, role.value)
                raise ConflictError(
                    f"This email already has a pending {existing.role.value} registration. "
                    "Verify that account, or wait for it to expire, before registering as a "
                    "different account type."
                )
            else:
                # Resume: same email, same role, still within the window.
                existing.password_hash = hash_password(data["password"])
                existing.first_name = first_name
                existing.last_name = last_name
                from src.extensions import db

                db.session.commit()
                return existing

        return UserRepository.create(
            email=data["email"],
            password_hash=hash_password(data["password"]),
            role=role,
            first_name=first_name,
            last_name=last_name,
        )

    @staticmethod
    def _send_verification_otp(user: User) -> None:
        """Never raises: a failed verification email must not roll back
        a successfully created account. The user can still request a
        resend once they realise nothing arrived."""
        from src.domains.auth.models.otp_verification import OTPPurpose
        from src.domains.auth.services.otp_service import OTPService

        try:
            OTPService.request_otp(destination=user.email, purpose=OTPPurpose.EMAIL_VERIFICATION)
        except Exception:  # noqa: BLE001
            current_app.logger.exception("Failed to send registration OTP for user %s", user.id)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    @staticmethod
    def login(email: str, password: str, ip_address: Optional[str] = None) -> Tuple[User, dict]:
        lockout_key = _login_lockout_key(email)
        max_attempts = current_app.config.get(
            "LOGIN_MAX_FAILED_ATTEMPTS", DEFAULT_LOGIN_MAX_FAILED_ATTEMPTS
        )
        lockout_window_seconds = (
            current_app.config.get("LOGIN_LOCKOUT_WINDOW_MINUTES", DEFAULT_LOGIN_LOCKOUT_WINDOW_MINUTES) * 60
        )

        if cache.get_count(lockout_key) >= max_attempts:
            audit.log_login_locked_out(email, ip_address)
            raise AccountLockedError(
                "Too many failed sign-in attempts. Please try again later.",
                data={"lockout_window_minutes": lockout_window_seconds // 60},
            )

        user = UserRepository.get_by_email(email)

        # An expired, never-verified account is treated as if it never
        # existed: cleaned up here too (not just at registration), so a
        # stale unverified row can't sit around indefinitely just because
        # nobody happened to re-register that address.
        if (
            user is not None
            and user.verification_status == VerificationStatus.UNVERIFIED
            and AuthService._is_unverified_expired(user)
        ):
            audit.log_unverified_account_expired(user.email)
            UserRepository.hard_delete(user)
            user = None

        if user is None or not verify_password(password, user.password_hash):
            cache.increment(lockout_key, ttl_seconds=lockout_window_seconds)
            audit.log_login_failed(email, ip_address)
            raise UnauthorizedError("Invalid email or password.")

        if user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account has been deactivated.")

        if user.verification_status != VerificationStatus.VERIFIED:
            audit.log_login_blocked_unverified(email, ip_address)
            expiry_hours = current_app.config.get(
                "UNVERIFIED_ACCOUNT_EXPIRY_HOURS", DEFAULT_UNVERIFIED_ACCOUNT_EXPIRY_HOURS
            )
            seconds_elapsed = (utcnow() - user.created_at).total_seconds()
            remaining_seconds = max(0, int(expiry_hours * 3600 - seconds_elapsed))
            raise EmailNotVerifiedError(
                "Please verify your email before signing in.",
                data={
                    "resend_available": True,
                    "verification_endpoint": "/auth/phone/request-otp",
                    "remaining_verification_seconds": remaining_seconds,
                },
            )

        # Success -- clear the failed-attempt counter for this email.
        cache.reset(lockout_key)
        UserRepository.update_last_login(user)
        tokens = AuthService._issue_tokens(user, ip_address=ip_address)
        audit.log_login_success(str(user.id), ip_address)
        return user, tokens

    # ------------------------------------------------------------------
    # JWT issuance
    # ------------------------------------------------------------------

    @staticmethod
    def _issue_tokens(
        user: User, device_id: Optional[str] = None, ip_address: Optional[str] = None
    ) -> dict:
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
    # Refresh Token rotation
    # ------------------------------------------------------------------

    @staticmethod
    def refresh(
        current_jti: str, user_id: str, device_id: Optional[str] = None, ip_address: Optional[str] = None
    ) -> dict:
        token_record = RefreshTokenRepository.get_by_jti_hash(_hash_jti(current_jti))

        if token_record is None or not token_record.is_valid():
            raise UnauthorizedError("Refresh token is invalid or has been revoked.")

        RefreshTokenRepository.revoke(token_record)

        user = UserRepository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found.")

        if user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account has been deactivated.")

        return AuthService._issue_tokens(user, device_id=device_id, ip_address=ip_address)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    @staticmethod
    def logout(user_id: str, refresh_token_jti: Optional[str] = None) -> None:
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
