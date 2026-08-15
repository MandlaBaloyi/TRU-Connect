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

TEMPLATE PATHS: template_name values below are relative to
src/shared/email/templates/, which is now grouped into per-domain
subfolders (auth/, business/, supplier/, ...) rather than a flat
directory -- "otp.html" alone would raise TemplateNotFound after that
reorganization, silently (EmailService.send_template swallows template
render errors so email failures never crash a caller), so this is worth
getting right rather than discovering it via "why didn't my OTP arrive."
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
from src.shared.audit import audit
from src.shared.constants.constants import MAX_OTP_EMAILS_PER_HOUR
from src.shared.email.email import EmailService

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
            template_name="auth/otp.html",
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
            if user.role == UserRole.SUPPLIER:
                OTPService._seed_supplier_profile(user)
            elif user.role == UserRole.BUSINESS:
                OTPService._seed_business_profile(user)
            OTPService._complete_network_invitations(user)

        # Local import: AuthService imports OTPService (for the
        # registration-time OTP send), so importing AuthService at
        # module level here would be circular.
        from src.domains.auth.services.auth_service import AuthService

        tokens = AuthService._issue_tokens(user)
        return user, tokens

    @staticmethod
    def _seed_business_profile(user: User) -> None:
        """Symmetric with _seed_supplier_profile above -- discovered
        while testing Supplier Approval end-to-end: a business that
        has never opened My Business has no BusinessProfile row
        either (that domain's own get_or_create_for_business is
        ALSO lazy-only, same reasoning as SupplierProfile's), so a
        supplier reviewing an incoming connection request would see
        "Unknown business" instead of a real name. Same fix, same
        placeholder-name reasoning, same guard, same resilience.

        ALSO seeds normalized_phone/normalized_email (added for Find
        Business) -- a freshly-created profile defaults to
        uses_same_as_account_phone/Email = True (the model's own
        column default), so the effective contact IS the account's own
        right now; without this, a newly-verified business would stay
        unsearchable until they happened to open My Business and touch
        their contact details, same class of bug the supplier-side
        auto-seed was originally built to close.
        """
        try:
            from src.domains.business.business_profile.repositories.business_profile_repository import (
                BusinessProfileRepository,
            )
            from src.domains.business.business_profile.services.business_profile_service import (
                _refresh_normalized_contact,
            )
            from src.extensions import db

            default_name = " ".join(filter(None, [user.first_name, user.last_name])).strip() or "New business"
            profile = BusinessProfileRepository.get_or_create_for_business(user.id, default_name=default_name)
            _refresh_normalized_contact(profile, user)
            db.session.commit()
        except Exception:  # noqa: BLE001
            current_app.logger.exception("Failed to seed business profile for user %s", user.id)

    @staticmethod
    def _complete_network_invitations(user: User) -> None:
        """Network Invitation (file.txt Phase 2), GENERALIZED to both
        directions -- the verification-success half of the two-stage
        link; see connections_service.py's own docstring for
        the full reasoning (registration only links; THIS is where the
        real, durable ConnectionRequest actually gets created, same
        timing rule as _seed_supplier_profile/_seed_business_profile
        above and for the identical reason). Called for BOTH roles now
        -- a supplier who was invited by a business, or a business who
        was invited by a supplier, both complete here. Never raises,
        same resilience pattern.
        """
        try:
            from src.domains.network.connections.services.connections_service import (
                complete_invitations_for_user,
            )

            complete_invitations_for_user(user.id, user.role.value)
        except Exception:  # noqa: BLE001
            current_app.logger.exception("Failed to complete network invitations for user %s", user.id)

    @staticmethod
    def _seed_supplier_profile(user: User) -> None:
        """Makes a newly-verified supplier findable via Supplier
        Discovery (file.txt Phase 1) the moment they're a real,
        confirmed account -- see supplier_profile_repository.py's own
        docstring on why this fires HERE (verification success) and
        not at raw registration.

        default_name uses user.first_name (== the "ownerName" the
        supplier gave at registration -- register_supplier maps it
        there, auth_service.py) as a readable placeholder. KNOWN GAP,
        not fixed here: SupplierRegisterSchema also collects a
        `business_name` field that Marshmallow validates but
        auth_service.py's _create_or_resume never actually persists
        anywhere -- by the time this hook runs (verification can
        happen minutes or hours after registration), that original
        request body is long gone, so there's nothing left to seed
        with here. The right fix is upstream (persist business_name
        somewhere at registration time, e.g. directly onto this
        profile via a get_or_create call in _create_or_resume itself);
        flagging it rather than reaching further than this fix's own
        scope to patch it.

        Never raises: matches _send_welcome_email's own reasoning
        exactly -- a seeding failure must not block the supplier's
        actual, already-succeeded verification/login.
        """
        try:
            from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
                SupplierProfileRepository,
            )

            SupplierProfileRepository.get_or_create_for_supplier(
                user.id, default_name=user.first_name or "New supplier"
            )
        except Exception:  # noqa: BLE001
            current_app.logger.exception("Failed to seed supplier profile for user %s", user.id)

    @staticmethod
    def _send_welcome_email(user: User) -> None:
        try:
            if user.role == UserRole.SUPPLIER:
                template_name = "supplier/welcome_supplier.html"
                context = {"owner_name": user.first_name}
            else:
                template_name = "business/welcome_business.html"
                context = {"first_name": user.first_name}

            EmailService.send_template(
                to=user.email, template_name=template_name, subject="Welcome to TRU Connect", context=context
            )
        except Exception:  # noqa: BLE001
            current_app.logger.exception("Failed to send welcome email for user %s", user.id)