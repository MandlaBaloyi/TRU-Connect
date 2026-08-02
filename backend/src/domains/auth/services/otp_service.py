"""
OTP Verification Service.
Ref: continuation master prompt (Phase 3), Step 13; "Shared Notification
Infrastructure" master prompt (welcome email); Auth Hardening master
prompt, Objective 1 (verify_otp now issues the first token pair).

Verifies by EMAIL, not phone -- frontend/mobile's registration does not
collect a phone number, so email is the only destination available at
this point in the flow.

WELCOME EMAIL: sent from here, only on the transition from unverified to
verified (never on a later re-verification).

TOKENS: register() no longer issues tokens (Auth Hardening, Objective 1)
-- there is no valid session for an unverified account. verify_otp() now
issues the first access/refresh pair on success, since proving control
of the email address is the first genuinely authenticated moment for a
brand-new account.

AUDIT
-----
request_otp() is the single entry point for both the initial
registration OTP and any later resend, so it always publishes
OTP_CREATED (a new code genuinely was generated either way) -- it has no
way to distinguish "first ever" from "resend" from inside this function
alone. If that distinction matters, the ROUTE that specifically handles
a resend button/endpoint should call audit.log_otp_resent() itself,
since it knows the caller's intent even though this service doesn't.

verify_otp() publishes OTP_VERIFIED on every successful code check, and
EMAIL_VERIFIED only on the genuine unverified->verified transition --
mirroring the existing was_already_verified check that already gates the
welcome email, so both follow exactly the same "never on re-verification"
rule.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Tuple

from flask import current_app

from src.core.base_model import utcnow
from src.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from src.domains.auth.models.otp_verification import OTPPurpose
from src.domains.auth.models.user import User, UserRole, VerificationStatus
from src.domains.auth.repositories.otp_repository import OTPRepository
from src.domains.auth.repositories.user_repository import UserRepository
from src.domains.auth.utils.otp import generate_numeric_otp, hash_otp, verify_otp_hash
from src.extensions import db
from src.shared import audit
from src.shared.constants import MAX_OTP_EMAILS_PER_HOUR
from src.shared.email import EmailService

OTP_EXPIRY_MINUTES = 10


class OTPService:
    @staticmethod
    def request_otp(destination: str, purpose: OTPPurpose = OTPPurpose.EMAIL_VERIFICATION) -> None:
        user = UserRepository.get_by_email(destination)
        if user is None:
            # Never reveal whether this destination has an account.
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
        audit.log_otp_created(str(user.id), destination)

        purpose_label = "email address" if purpose == OTPPurpose.EMAIL_VERIFICATION else "phone number"
        EmailService.send_template(
            to=destination,
            template_name="otp.html",
            subject="Your TRU Connect verification code",
            context={"otp_code": code, "purpose_label": purpose_label, "expiry_minutes": OTP_EXPIRY_MINUTES},
            rate_limit_key=f"otp:{destination}",
            rate_limit_max=MAX_OTP_EMAILS_PER_HOUR,
            rate_limit_window_seconds=3600,
        )

    @staticmethod
    def verify_otp(
        destination: str, code: str, purpose: OTPPurpose = OTPPurpose.EMAIL_VERIFICATION
    ) -> Tuple[User, dict]:
        user = UserRepository.get_by_email(destination)
        if user is None:
            raise NotFoundError("No account found for this destination.")

        record = OTPRepository.get_latest_active(user.id, purpose)
        if record is None:
            audit.log_otp_failed(destination, "no_pending_otp")
            raise UnauthorizedError("No pending verification code found. Please request a new one.")

        if record.is_expired():
            audit.log_otp_failed(destination, "expired")
            raise UnauthorizedError("This verification code has expired. Please request a new one.")

        if not record.has_attempts_remaining():
            audit.log_otp_failed(destination, "too_many_attempts")
            raise ForbiddenError("Too many incorrect attempts. Please request a new verification code.")

        if record.destination != destination or not verify_otp_hash(code, record.otp_code_hash):
            OTPRepository.increment_attempts(record)
            audit.log_otp_failed(destination, "incorrect_code")
            raise UnauthorizedError("Incorrect verification code.")

        OTPRepository.mark_used(record)

        was_already_verified = user.verification_status == VerificationStatus.VERIFIED
        user.verification_status = VerificationStatus.VERIFIED
        db.session.commit()

        audit.log_otp_verified(str(user.id), destination)

        if not was_already_verified:
            audit.log_email_verified(str(user.id), destination)
            OTPService._send_welcome_email(user)

        # Local import: AuthService imports OTPService (for the
        # registration-time OTP send), so importing AuthService at
        # module level here would be circular.
        from src.domains.auth.services.auth_service import AuthService

        tokens = AuthService._issue_tokens(user)
        return user, tokens

    @staticmethod
    def _send_welcome_email(user: User) -> None:
        try:
            if user.role == UserRole.SUPPLIER:
                template_name = "welcome_supplier.html"
                context = {"owner_name": user.first_name}
            else:
                template_name = "welcome_business.html"
                context = {"first_name": user.first_name}

            EmailService.send_template(
                to=user.email, template_name=template_name, subject="Welcome to TRU Connect", context=context
            )
        except Exception:  # noqa: BLE001
            current_app.logger.exception("Failed to send welcome email for user %s", user.id)