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
# Added for Supplier Invitation (file.txt Phase 2) -- a business
# inviting suppliers is a real, bounded action, same reasoning as
# every other outbound-email limit above.
MAX_SUPPLIER_INVITATIONS_PER_HOUR = 10

# --- Auth Hardening additions ---
DEFAULT_UNVERIFIED_ACCOUNT_EXPIRY_HOURS = 24
DEFAULT_LOGIN_MAX_FAILED_ATTEMPTS = 5
DEFAULT_LOGIN_LOCKOUT_WINDOW_MINUTES = 15
DEFAULT_PASSWORD_RESET_TICKET_EXPIRY_HOURS = 1
# Longer than password reset (1 hour) on purpose -- an invitation is
# addressed to someone who may not check email as urgently as someone
# actively mid-password-reset; file.txt's own invitation flow assumes
# a supplier might take real time to notice and act on it.
DEFAULT_SUPPLIER_INVITATION_EXPIRY_HOURS = 168  # 7 days

# --- Connection request retry-after-decline (network/connections) ---
# A DECLINED request isn't final forever, but retrying isn't free
# either -- these bound how many times someone can ask again after
# being declined, so retrying can't become a way to pressure or spam
# the person who said no. Both windows are checked independently
# against the SAME retry_history array (ConnectionRequest.retry_history)
# -- a retry only succeeds if it's within BOTH limits, not just one.
# PROVISIONAL, like every other not-yet-finalised limit in this
# codebase (see e.g. MAX_SUPPLIER_INVITATIONS_PER_HOUR's own
# reasoning) -- these are sensible starting numbers, not a committed
# final policy.
MAX_CONNECTION_RETRY_PER_DAY = 1
MAX_CONNECTION_RETRY_PER_WEEK = 3
