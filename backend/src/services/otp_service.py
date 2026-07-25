"""
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
