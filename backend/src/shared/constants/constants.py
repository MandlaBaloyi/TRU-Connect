"""
Notification + Auth Hardening defaults.
MailProvider,
mail defaults, rate limits; Auth Hardening,
.

These are DEFAULTS, used when the corresponding environment variable /
app.config value is not set. The authoritative, overridable versions
live in src/config.py (APP_BASE_URL, UNVERIFIED_ACCOUNT_EXPIRY_HOURS,
LOGIN_MAX_FAILED_ATTEMPTS, LOGIN_LOCKOUT_WINDOW_MINUTES,
PASSWORD_RESET_TICKET_EXPIRY_HOURS) -- these module-level constants exist
as fallbacks for any code path that runs outside an app context.
"""
from __future__ import annotations

import enum


class MailProvider(str, enum.Enum):
    SMTP = "smtp"
    SES = "ses"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    AZURE = "azure"
    FAKE = "fake"


DEFAULT_MAIL_TIMEOUT_SECONDS = 10
DEFAULT_MAIL_MAX_RETRIES = 3
DEFAULT_MAIL_RETRY_DELAYS_SECONDS = [5, 15, 60]

MAX_OTP_EMAILS_PER_HOUR = 5
MAX_PASSWORD_RESET_EMAILS_PER_HOUR = 3
MAX_WELCOME_EMAILS_PER_ACCOUNT = 1
MAX_EMAILS_PER_USER_PER_HOUR = 10

# --- Auth Hardening additions ---
DEFAULT_UNVERIFIED_ACCOUNT_EXPIRY_HOURS = 24
DEFAULT_LOGIN_MAX_FAILED_ATTEMPTS = 5
DEFAULT_LOGIN_LOCKOUT_WINDOW_MINUTES = 15
DEFAULT_PASSWORD_RESET_TICKET_EXPIRY_HOURS = 1
