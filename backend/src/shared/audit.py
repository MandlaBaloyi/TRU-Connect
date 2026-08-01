"""
Security / audit event logging.
Ref: Auth Hardening master prompt, Objective 9.

Distinct from src/shared/monitoring.py, which is specifically the email
DELIVERY lifecycle (queued/sent/failed/retry). This module is general
authentication and security event logging: logins, lockouts,
verification-gate hits, password resets, account expiry cleanup.

Never logs a password, OTP code, reset ticket, or JWT -- only identifiers
(masked email, user id) and IP address, matching the same "never log
sensitive values" rule the email infrastructure already follows.
"""
from __future__ import annotations

from typing import Optional

from src.shared.helpers import mask_email

import logging

logger = logging.getLogger("tru_connect.audit")


def log_login_success(user_id: str, ip_address: Optional[str]) -> None:
    logger.info("login_success user_id=%s ip=%s", user_id, ip_address or "unknown")


def log_login_failed(email: str, ip_address: Optional[str]) -> None:
    logger.warning("login_failed email=%s ip=%s", mask_email(email), ip_address or "unknown")


def log_login_locked_out(email: str, ip_address: Optional[str]) -> None:
    logger.warning("login_locked_out email=%s ip=%s", mask_email(email), ip_address or "unknown")


def log_login_blocked_unverified(email: str, ip_address: Optional[str]) -> None:
    logger.info("login_blocked_unverified email=%s ip=%s", mask_email(email), ip_address or "unknown")


def log_unverified_account_expired(email: str) -> None:
    logger.info("unverified_account_expired email=%s", mask_email(email))


def log_registration_role_conflict(email: str, existing_role: str, attempted_role: str) -> None:
    logger.info(
        "registration_role_conflict email=%s existing_role=%s attempted_role=%s",
        mask_email(email),
        existing_role,
        attempted_role,
    )


def log_password_reset_requested(email: str) -> None:
    logger.info("password_reset_requested email=%s", mask_email(email))


def log_password_reset_completed(user_id: str) -> None:
    logger.info("password_reset_completed user_id=%s", user_id)
