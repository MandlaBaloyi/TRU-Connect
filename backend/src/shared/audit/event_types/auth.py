"""
Auth's own audit event vocabulary -- moved here from the single
89-line flat AuditEventName enum that used to hold every domain's
events together, organized only by comment headers. Lives in
shared/audit/ rather than domains/auth/ deliberately: this is the
neutral ground both Auth (the publisher) and Security (the consumer)
import from, which is what keeps the dependency arrow correct -- Auth
never imports Security, Security never imports Auth, both import this.

NOTE ON COVERAGE: not all values below have a publisher yet. Most map
to real code paths today. The ACCOUNT_*/ROLE_*/PERMISSION_* values are
declared but nothing publishes them yet, because no admin
account-management feature exists -- declared now so the enum (and any
admin-panel filter UI built against it) doesn't need to change when
that feature lands.
"""
from __future__ import annotations

import enum


class AuthAuditEvent(str, enum.Enum):
    # --- Registration ---
    REGISTER_REQUESTED = "auth.register_requested"
    REGISTER_SUCCESS = "auth.register_success"
    REGISTER_FAILED = "auth.register_failed"
    REGISTER_ROLE_CONFLICT = "auth.register_role_conflict"
    REGISTER_RESUMED = "auth.register_resumed"

    # --- Email verification ---
    EMAIL_VERIFICATION_SENT = "auth.email_verification_sent"
    EMAIL_VERIFIED = "auth.email_verified"
    EMAIL_VERIFICATION_FAILED = "auth.email_verification_failed"
    EMAIL_VERIFICATION_EXPIRED = "auth.email_verification_expired"

    # --- OTP ---
    OTP_CREATED = "auth.otp_created"
    OTP_SENT = "auth.otp_sent"
    OTP_VERIFIED = "auth.otp_verified"
    OTP_FAILED = "auth.otp_failed"
    OTP_RESENT = "auth.otp_resent"
    OTP_EXPIRED = "auth.otp_expired"

    # --- Login ---
    LOGIN_SUCCESS = "auth.login_success"
    LOGIN_FAILED = "auth.login_failed"
    LOGIN_BLOCKED = "auth.login_blocked"
    LOGIN_LOCKED = "auth.login_locked"
    LOGIN_RATE_LIMITED = "auth.login_rate_limited"
    LOGIN_UNVERIFIED = "auth.login_unverified"
    # V2: correct password, right account, WRONG SURFACE -- a business
    # signing in at the supplier web portal. Its own event because it is
    # not a failed sign-in and must not read like one when someone is
    # scanning for attacks; it is a person on the wrong door.
    LOGIN_WRONG_PORTAL = "auth.login_wrong_portal"

    # --- Rate limiting ---
    REGISTER_RATE_LIMITED = "auth.register_rate_limited"
    REFRESH_RATE_LIMITED = "auth.refresh_rate_limited"
    PASSWORD_RESET_REQUEST_RATE_LIMITED = "auth.password_reset_request_rate_limited"
    PASSWORD_RESET_RATE_LIMITED = "auth.password_reset_rate_limited"
    OTP_REQUEST_RATE_LIMITED = "auth.otp_request_rate_limited"
    OTP_VERIFY_RATE_LIMITED = "auth.otp_verify_rate_limited"

    # --- Password reset ---
    PASSWORD_RESET_REQUESTED = "auth.password_reset_requested"
    PASSWORD_RESET_TOKEN_CREATED = "auth.password_reset_token_created"
    PASSWORD_RESET_SUCCESS = "auth.password_reset_success"
    PASSWORD_RESET_FAILED = "auth.password_reset_failed"
    PASSWORD_RESET_EXPIRED = "auth.password_reset_expired"

    # --- Tokens ---
    TOKEN_CREATED = "auth.token_created"
    TOKEN_REFRESHED = "auth.token_refreshed"
    TOKEN_REVOKED = "auth.token_revoked"
    TOKEN_EXPIRED = "auth.token_expired"

    # --- Logout ---
    LOGOUT = "auth.logout"
    LOGOUT_ALL_DEVICES = "auth.logout_all_devices"

    # --- Account administration (no publisher yet -- see module docstring) ---
    ACCOUNT_ENABLED = "auth.account_enabled"
    ACCOUNT_DISABLED = "auth.account_disabled"
    ACCOUNT_DELETED = "auth.account_deleted"
    ACCOUNT_UNLOCKED = "auth.account_unlocked"
    ROLE_CHANGED = "auth.role_changed"
    PERMISSION_CHANGED = "auth.permission_changed"

    # --- API keys (V2: the machine door -- a supplier's own ERP) ---
    #
    # A key is a long-lived credential a human never types, which is
    # exactly why its lifecycle needs a paper trail: CREATED and REVOKED
    # are the two moments a supplier will one day need to prove, and
    # AUTH_FAILED is what a brute-force attempt against the integration
    # endpoint actually looks like.
    API_KEY_CREATED = "auth.api_key_created"
    API_KEY_REVOKED = "auth.api_key_revoked"
    API_KEY_AUTH_FAILED = "auth.api_key_auth_failed"
    API_KEY_SCOPE_DENIED = "auth.api_key_scope_denied"

    # --- Platform / system, auth-owned lifecycle sweep ---
    UNVERIFIED_ACCOUNT_EXPIRED = "auth.unverified_account_expired"
