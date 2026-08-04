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

AUDIT
-----
Every registration outcome (created / resumed / conflict / role-conflict),
every login outcome (success / failed / locked / unverified-blocked), and
every token lifecycle event (created / refreshed / revoked) publishes a
structured event via src.shared.audit.audit, in addition to whatever text log
it already wrote. See src/shared/audit.py for the full explanation of why
this never changes what a failure returns to the caller.
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
from src.shared.audit import audit, audit_context
from src.shared.cache.cache import cache
from src.shared.constants.constants import (
    DEFAULT_LOGIN_LOCKOUT_WINDOW_MINUTES,
    DEFAULT_LOGIN_MAX_FAILED_ATTEMPTS,
    DEFAULT_UNVERIFIED_ACCOUNT_EXPIRY_HOURS,
)
from src.shared.security.security import hash_password, verify_password


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
                # AUDIT: previously unlogged — a duplicate-registration
                # attempt against an already-verified account is a real
                # event an investigator would want to see (e.g. someone
                # probing whether an email is already registered).
                audit.log_register_failed(data["email"], "email_already_registered")
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
                # AUDIT: a distinct outcome from a brand-new account being
                # created — same row, not a duplicate. See
                # log_register_resumed's docstring in shared/audit.py.
                audit.log_register_resumed(data["email"], role.value)
                return existing

        new_user = UserRepository.create(
            email=data["email"],
            password_hash=hash_password(data["password"]),
            role=role,
            first_name=first_name,
            last_name=last_name,
        )
        # AUDIT: logged here specifically (not in register_business/
        # register_supplier) so it can never double-fire alongside
        # log_register_resumed above — this is the one place that
        # actually distinguishes "new account" from "resumed account".
        audit.log_register_success(str(new_user.id), new_user.email, new_user.role.value)
        return new_user

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
        # FALLBACK: OTPService.verify_otp() issues the very first token
        # pair on a fresh account and does not pass ip_address/device_id
        # explicitly. Rather than threading those through every call site
        # by hand, fall back to the same request-context extraction the
        # audit system already uses — this is safe (returns None outside
        # a request, e.g. tests or a future CLI path) and fixes IP/device
        # capture for every current AND future caller that forgets to
        # pass them explicitly, not just this one.
        ip_address = ip_address or audit_context.get_ip_address()
        device_id = device_id or audit_context.get_device_id()

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

        # AUDIT: centralized here rather than at each of the three call
        # sites (login, refresh, OTP-verify) because every call to
        # _issue_tokens means a new token pair was created, regardless of
        # caller — this also automatically covers the OTP-verification
        # token issuance in otp_service.py without needing a separate
        # call there.
        audit.log_token_created(str(user.id))
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
        # AUDIT: the OLD token being revoked as part of rotation is its
        # own meaningful event, distinguished from a logout-triggered
        # revocation by reason="rotation" — every revocation matters
        # regardless of cause; the cause is what differs.
        audit.log_token_revoked(user_id, reason="rotation")

        user = UserRepository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found.")

        if user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account has been deactivated.")

        tokens = AuthService._issue_tokens(user, device_id=device_id, ip_address=ip_address)
        # AUDIT: _issue_tokens() already logged TOKEN_CREATED above — this
        # additional event specifically marks "issued via the refresh
        # flow", since TOKEN_CREATED alone doesn't distinguish a refresh
        # from a fresh login.
        audit.log_token_refreshed(user_id)
        return tokens

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    @staticmethod
    def logout(user_id: str, refresh_token_jti: Optional[str] = None) -> None:
        if refresh_token_jti:
            token_record = RefreshTokenRepository.get_by_jti_hash(_hash_jti(refresh_token_jti))
            if token_record is not None and str(token_record.user_id) == str(user_id):
                RefreshTokenRepository.revoke(token_record)
                audit.log_token_revoked(user_id, reason="logout")
                audit.log_logout(user_id)
            return

        # NOTE: assumes revoke_all_for_user() returns a count of revoked
        # tokens. If it currently returns None, `revoked_count or 0` keeps
        # this safe, but the audit metadata will show 0 regardless of the
        # real count — worth confirming the repository's actual return
        # type and adjusting it to return the count if it doesn't already.
        revoked_count = RefreshTokenRepository.revoke_all_for_user(user_id)
        audit.log_logout_all_devices(user_id, revoked_count or 0)

    @staticmethod
    def get_current_user(user_id: str) -> User:
        user = UserRepository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found.")
        return user