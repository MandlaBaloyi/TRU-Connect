"""
Forgot/Reset Password Service.


NAMING NOTE: the physical database column remains
PasswordResetToken.token_hash (no migration -- see
src/shared/tickets.py's module docstring for the full rationale).
"ticket" is the external, API-facing name only; this file is the single
place that bridges the two.

RESET URL: built from APP_BASE_URL (src/config.py) + "/reset-password",
handled by src/domains/platform/api/reset_redirect_routes.py.

UNVERIFIED-ACCOUNT BRANCH
--------------------------
An unverified account has never proven control of its email, and login
is already blocked for it regardless of password -- issuing a password
reset ticket to it doesn't unlock anything real.

forgot_password() branches on verification_status:
  - VERIFIED account   -> unchanged: generates a reset ticket, sends
                          password_reset.html.
  - UNVERIFIED account -> sends resume_registration.html instead: a
                          plain instructional email pointing the user
                          back to registration (which already resumes
                          their existing unverified account and resends
                          a fresh OTP -- see AuthService._create_or_resume).
                          Deliberately NOT an OTP: forgot-password and
                          registration must not become two parallel ways
                          to obtain a verification code for the same
                          account.
  - No account found   -> unchanged: does nothing.

Both send-paths share the SAME rate limit key
(f"password_reset:{email}") -- from the account owner's inbox, "resend
my OTP" and "send me a reset link" are the same limited resource
(repeated forgot-password submissions against their email), and both
must be equally protected from abuse.

The RESPONSE the caller (the route) sees is IDENTICAL in all three
cases -- this method always returns None, never raises, and never
reveals which branch was taken. Enumeration-safety is unaffected; only
the internal behaviour, and which email template is used, changed.

TEMPLATE PATHS: template_name values below are relative to
src/shared/email/templates/, which is grouped into per-domain
subfolders (auth/, business/, supplier/, ...) rather than a flat
directory -- both templates used here live under auth/.
"""
from __future__ import annotations

from flask import current_app

from src.core.exceptions import TicketInvalidError
from src.domains.auth.models.user import VerificationStatus
from src.domains.auth.repositories.password_reset_repository import PasswordResetRepository
from src.domains.auth.repositories.refresh_token_repository import RefreshTokenRepository
from src.domains.auth.repositories.user_repository import UserRepository
from src.extensions import db
from src.shared.audit import audit
from src.shared.constants.constants import DEFAULT_PASSWORD_RESET_TICKET_EXPIRY_HOURS, MAX_PASSWORD_RESET_EMAILS_PER_HOUR
from src.shared.email.email import EmailService
from src.shared.security.security import hash_password
from src.shared.tickets.tickets import create_ticket, hash_ticket, is_ticket_expired, ticket_expiry


class PasswordResetService:
    @staticmethod
    def forgot_password(email: str) -> None:
        """Enumeration-safe: behaves identically from the caller's point
        of view (returns None, no exception) regardless of which of the
        three cases below actually applied."""
        user = UserRepository.get_by_email(email)
        if user is None:
            return

        if user.verification_status != VerificationStatus.VERIFIED:
            EmailService.send_template(
                to=email,
                template_name="auth/resume_registration.html",
                subject="Verify your TRU Connect account",
                context={},
                rate_limit_key=f"password_reset:{email}",
                rate_limit_max=MAX_PASSWORD_RESET_EMAILS_PER_HOUR,
                rate_limit_window_seconds=3600,
            )
            return

        expiry_hours = current_app.config.get(
            "PASSWORD_RESET_TICKET_EXPIRY_HOURS", DEFAULT_PASSWORD_RESET_TICKET_EXPIRY_HOURS
        )
        raw_ticket = create_ticket()
        expires_at = ticket_expiry(hours=expiry_hours)
        PasswordResetRepository.create(user_id=user.id, token_hash=hash_ticket(raw_ticket), expires_at=expires_at)

        base_url = current_app.config.get("APP_BASE_URL", "http://localhost:5000")
        reset_url = f"{base_url}/reset-password?ticket={raw_ticket}"

        audit.log_password_reset_requested(email)

        EmailService.send_template(
            to=email,
            template_name="auth/password_reset.html",
            subject="Reset your TRU Connect password",
            context={"reset_url": reset_url, "expiry_hours": expiry_hours},
            rate_limit_key=f"password_reset:{email}",
            rate_limit_max=MAX_PASSWORD_RESET_EMAILS_PER_HOUR,
            rate_limit_window_seconds=3600,
        )

    @staticmethod
    def validate_ticket(ticket: str) -> bool:
        """Read-only check -- lets the mobile app show "this link has
        expired" immediately on screen load, rather than only after the
        user fills in a new password and submits."""
        record = PasswordResetRepository.get_by_token_hash(hash_ticket(ticket))
        return record is not None and not record.is_used and not is_ticket_expired(record.expires_at)

    @staticmethod
    def reset_password(ticket: str, new_password: str) -> None:
        record = PasswordResetRepository.get_by_token_hash(hash_ticket(ticket))

        if record is None or record.is_used or is_ticket_expired(record.expires_at):
            raise TicketInvalidError("This password reset link is invalid or has expired.")

        user = UserRepository.get_by_id(record.user_id)
        if user is None:
            raise TicketInvalidError("This password reset link is invalid or has expired.")

        user.password_hash = hash_password(new_password)
        db.session.commit()

        PasswordResetRepository.mark_used(record)
        RefreshTokenRepository.revoke_all_for_user(user.id)

        audit.log_password_reset_completed(str(user.id))