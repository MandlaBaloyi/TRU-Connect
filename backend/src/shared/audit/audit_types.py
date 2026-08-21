"""
Audit event contracts — neutral ground.

Both publishers (Auth today; Business, Supplier, Marketplace, Wallet later)
and the consumer (Security's audit service) import from here. Living in
shared/ is what keeps the dependency arrow correct: Auth never imports
Security, Security never imports Auth, both import these types.

Nothing in this file is Authentication-specific. Event names are namespaced
by domain so future domains extend the enum without colliding.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


class AuditDomain(str, enum.Enum):
    """Which domain the event originated from. Every future domain adds a
    value here — the audit table itself never changes."""
    AUTH = "auth"
    BUSINESS = "business"
    SUPPLIER = "supplier"
    MARKETPLACE = "marketplace"
    TRUST = "trust"
    VERIFICATION = "verification"
    PLATFORM = "platform"
    SECURITY = "security"
    # Added for network/connections (file.txt Phase 1) -- a
    # cross-cutting domain like SECURITY/PLATFORM, not owned by
    # Business or Supplier alone since the relationship belongs to
    # both sides equally.
    NETWORK = "network"


class ActorType(str, enum.Enum):
    """WHO performed the action — distinct from user_id, which may be null
    for the same event (e.g. a failed login for an email that doesn't
    exist has an actor_type of USER but no user_id).

    Deliberately included from day one: this cannot be reconstructed from
    historical rows later, because "was this a human or the 3am cleanup
    job?" is not derivable after the fact.
    """
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
    SCHEDULER = "scheduler"
    API = "api"
    INTEGRATION = "integration"
    ANONYMOUS = "anonymous"  # request with no authenticated identity yet


class AuditCategory(str, enum.Enum):
    """Coarse grouping for dashboard filtering ("show me all authentication
    events") — deliberately broader than event names."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ACCOUNT_MANAGEMENT = "account_management"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


class AuditSeverity(str, enum.Enum):
    """How much an investigator should care. Drives dashboard colour-coding
    and future alert thresholds."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class AuditEventName(str, enum.Enum):
    """
    Every event the platform can emit. Namespaced by domain prefix so
    future domains extend this without collision.

    NOTE ON COVERAGE: not all values below have a publisher yet. Auth
    events map to real code paths today (or will as call sites are added).
    The ACCOUNT_* / ROLE_* / PERMISSION_* values are defined here but
    nothing publishes them, because no admin account-management feature
    exists yet — they are declared now so the enum (and any admin-panel
    filter UI built against it) does not need to change when that feature
    lands.
    """

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

    # --- Rate limiting (added alongside LOGIN_RATE_LIMITED, which
    # already existed pre-declared with no publisher — see this class's
    # own docstring on that pattern. Same naming convention, one per
    # rate-limited route rather than one generic catch-all, matching
    # how LOGIN_FAILED/LOGIN_LOCKED/LOGIN_UNVERIFIED are already split
    # by specific cause rather than collapsed into one event.) ---
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

    # --- Account administration (no publisher yet — see class docstring) ---
    ACCOUNT_ENABLED = "auth.account_enabled"
    ACCOUNT_DISABLED = "auth.account_disabled"
    ACCOUNT_DELETED = "auth.account_deleted"
    ACCOUNT_UNLOCKED = "auth.account_unlocked"
    ROLE_CHANGED = "auth.role_changed"
    PERMISSION_CHANGED = "auth.permission_changed"

    # --- Platform / system ---
    UNVERIFIED_ACCOUNT_EXPIRED = "auth.unverified_account_expired"
    SCHEDULED_JOB_COMPLETED = "platform.scheduled_job_completed"
    SCHEDULED_JOB_FAILED = "platform.scheduled_job_failed"

    # --- Network / Supplier Discovery (file.txt Phase 1) ---
    SUPPLIER_SEARCH_RATE_LIMITED = "network.supplier_search_rate_limited"
    CONNECTION_REQUEST_RATE_LIMITED = "network.connection_request_rate_limited"
    # Reverse direction (supplier searching for businesses, Find Business).
    # Deliberately a distinct event from SUPPLIER_SEARCH_RATE_LIMITED above
    # rather than reusing it -- that name means "the supplier-search action
    # got rate-limited" (business searching FOR suppliers), which is not
    # what's happening here. This event name mirrors it for the other
    # direction: the business-search action (supplier searching FOR
    # businesses) getting rate-limited.
    BUSINESS_SEARCH_RATE_LIMITED = "network.business_search_rate_limited"

    # --- Supplier / Products ---
    PRODUCT_CREATE_RATE_LIMITED = "supplier.product_create_rate_limited"
    PRODUCT_BULK_ACTION_RATE_LIMITED = "supplier.product_bulk_action_rate_limited"
    INVENTORY_ADJUST_RATE_LIMITED = "supplier.inventory_adjust_rate_limited"
    MEDIA_SIGN_RATE_LIMITED = "supplier.media_sign_rate_limited"
    PRODUCT_MEDIA_REJECTED = "supplier.product_media_rejected"
    BULK_IMPORT_SUBMIT_RATE_LIMITED = "supplier.bulk_import_submit_rate_limited"
    MEDIA_ORPHAN_ASSET_CLEANED = "media.orphan_asset_cleaned"


@dataclass
class AuditEvent:
    """
    One audit record, in transit. Mirrors the audit_events table but is a
    plain dataclass so publishers never touch SQLAlchemy — Auth builds one
    of these and hands it to shared.audit.publish(); only Security's
    repository knows it becomes a database row.

    Almost everything is Optional by design. A scheduled-job event has no
    IP or user agent; a failed login for a nonexistent email has no
    user_id. Requiring those would make this un-generic, which is exactly
    what the "one enterprise audit table" design is trying to avoid.
    """

    # --- Required: the irreducible minimum for a usable audit record ---
    event_name: AuditEventName
    domain: AuditDomain
    status: AuditStatus

    # --- Classification (defaulted from rules/event_config.py) ---
    category: Optional[AuditCategory] = None
    severity: Optional[AuditSeverity] = None
    module: Optional[str] = None  # e.g. "auth_service", "otp_service"

    # --- When ---
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # --- Who ---
    actor_type: ActorType = ActorType.USER
    user_id: Optional[str] = None
    email: Optional[str] = None  # FULL email, never masked — masking is a
                                  # presentation concern (logs/UI), never storage.
                                  # Investigators must be able to search exact values.
    role: Optional[str] = None
    tenant_id: Optional[str] = None  # nullable today; TRU Connect is not
                                      # multi-tenant yet, but retrofitting a
                                      # tenant column across table+indexes+
                                      # repository+API+permissions later is
                                      # far more expensive than carrying it now.

    # --- Where from ---
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    browser: Optional[str] = None
    operating_system: Optional[str] = None
    platform: Optional[str] = None
    device_id: Optional[str] = None

    # --- Request correlation ---
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None  # stitches multi-step flows
                                           # (register -> OTP sent -> verified)
                                           # into one story in the admin UI
    request_id: Optional[str] = None
    http_method: Optional[str] = None
    endpoint: Optional[str] = None
    http_status_code: Optional[int] = None

    # --- Outcome ---
    failure_reason: Optional[str] = None

    # --- Extensibility ---
    metadata: dict[str, Any] = field(default_factory=dict)
