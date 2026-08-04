"""
Structured event logging for the email lifecycle.
"Shared Notification Infrastructure"  "LOGGING" --
"Every email attempt must be logged... Email queued, Email sent, Email
failed, Retry scheduled, SMTP timeout, SMTP authentication failure... Use
structured logging." and "SECURITY" -- "Never log: OTP codes, Reset
tokens, Passwords, SMTP passwords, JWTs."

DESIGN
------
Thin wrapper around Python's standard logging module (uses the same
logger namespace convention as src/shared/logger.py's configure_logging)
that (a) always logs in a consistent, structured (key=value) shape, and
(b) is the ONLY place email-lifecycle log lines are produced, so the
"never log sensitive values" rule only has to be enforced in one place.
Callers pass a masked destination (see src/shared/helpers.py:mask_email)
and a template name -- never raw OTP codes, tokens, or credentials.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("tru_connect.email")


def log_email_queued(destination_masked: str, template_name: str) -> None:
    logger.info("email_queued destination=%s template=%s", destination_masked, template_name)


def log_email_sent(destination_masked: str, template_name: str, duration_seconds: float) -> None:
    logger.info(
        "email_sent destination=%s template=%s duration_ms=%.1f",
        destination_masked,
        template_name,
        duration_seconds * 1000,
    )


def log_email_failed(destination_masked: str, template_name: str, reason: str) -> None:
    logger.warning("email_failed destination=%s template=%s reason=%s", destination_masked, template_name, reason)


def log_retry_scheduled(destination_masked: str, template_name: str, attempt: int, delay_seconds: int) -> None:
    logger.warning(
        "email_retry_scheduled destination=%s template=%s attempt=%s delay_seconds=%s",
        destination_masked,
        template_name,
        attempt,
        delay_seconds,
    )


def log_smtp_timeout(destination_masked: str) -> None:
    logger.error("smtp_timeout destination=%s", destination_masked)


def log_smtp_auth_failure() -> None:
    """Deliberately takes no destination/credential arguments -- an auth
    failure is a provider-level problem, not specific to one recipient,
    and must never risk logging a password."""
    logger.error("smtp_authentication_failure")


def log_rate_limit_exceeded(destination_masked: str, template_name: str) -> None:
    logger.warning("email_rate_limit_exceeded destination=%s template=%s", destination_masked, template_name)
