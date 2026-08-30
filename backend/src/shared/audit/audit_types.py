"""
Audit event contracts — neutral ground.

Both publishers (Auth today; Business, Supplier, Marketplace, Wallet later)
and the consumer (Security's audit service) import from here. Living in
shared/ is what keeps the dependency arrow correct: Auth never imports
Security, Security never imports Auth, both import these types.

Nothing in this file is Authentication-specific. Event NAME VALUES
themselves live in shared/audit/event_types/ (one small file per real
domain), not here -- this file holds the DOMAIN-AGNOSTIC transport
contract (AuditEvent, AuditDomain, ActorType, AuditCategory,
AuditSeverity, AuditStatus) that every domain's events share regardless
of their own specific names.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Union

from src.shared.audit.event_types.auth import AuthAuditEvent
from src.shared.audit.event_types.business import BusinessAuditEvent
from src.shared.audit.event_types.network import NetworkAuditEvent
from src.shared.audit.event_types.platform import PlatformAuditEvent
from src.shared.audit.event_types.supplier import SupplierAuditEvent

# Accepts any real domain's event enum -- used as AuditEvent.event_name's
# own type hint below, and by anything else (e.g. security/audit/rules/
# event_config.py's own get_policy) that needs to accept an event name
# from ANY domain, not just one. Grows by one member when a new domain
# gets its own event_types/ file -- nothing else about this file changes.
AuditEventNameType = Union[AuthAuditEvent, BusinessAuditEvent, NetworkAuditEvent, PlatformAuditEvent, SupplierAuditEvent]


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


# AuditEventName (the single flat 89-line enum every domain's events
# used to live in together) is GONE -- moved to shared/audit/event_types/,
# one small file per domain that actually publishes events (auth.py,
# supplier.py, network.py, platform.py). See event_types/__init__.py's
# own docstring for the full reasoning. Import the specific domain enum
# directly instead (e.g. `from src.shared.audit.event_types.auth import
# AuthAuditEvent`), or use AuditEventNameType below when a type hint
# needs to accept any of them.


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
    event_name: AuditEventNameType
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
