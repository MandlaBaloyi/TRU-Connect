"""
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
