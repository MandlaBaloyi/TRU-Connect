"""
Per-event policy: category, severity, and write mode. Relocated from
security/rules/ to security/audit/rules/ -- this is audit-specific
policy, distinct from security/rules/thresholds.py (a general Auth
threshold), which correctly stays where it is.
"""

from __future__ import annotations

import enum
from typing import NamedTuple

from src.shared.audit.audit_types import AuditCategory, AuditEventNameType, AuditSeverity
from src.shared.audit.event_types.auth import AuthAuditEvent


class WriteMode(str, enum.Enum):
    SYNC = "sync"
    ASYNC = "async"


class EventPolicy(NamedTuple):
    category: AuditCategory
    severity: AuditSeverity
    write_mode: WriteMode


DEFAULT_POLICY = EventPolicy(AuditCategory.SYSTEM, AuditSeverity.INFO, WriteMode.SYNC)

EVENT_POLICIES: dict[AuditEventNameType, EventPolicy] = {
    AuthAuditEvent.LOGIN_SUCCESS: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuthAuditEvent.UNVERIFIED_ACCOUNT_EXPIRED: EventPolicy(AuditCategory.SYSTEM, AuditSeverity.INFO, WriteMode.ASYNC),
    # Rate-limit violations -- AUTHENTICATION category (every Phase 1
    # limited route is an auth route) and MEDIUM severity: a real
    # signal worth an investigator's attention, but on its own not yet
    # the CRITICAL-tier event a confirmed account compromise would be.
    AuthAuditEvent.LOGIN_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuthAuditEvent.REGISTER_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuthAuditEvent.REFRESH_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuthAuditEvent.PASSWORD_RESET_REQUEST_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuthAuditEvent.PASSWORD_RESET_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuthAuditEvent.OTP_REQUEST_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuthAuditEvent.OTP_VERIFY_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    # --- V2: web portal + API keys ---
    #
    # WRONG_PORTAL is INFO, not MEDIUM, and that is the whole reason it
    # is listed here rather than left on the default: it is a person at
    # the wrong door with correct credentials. Filing it at the same
    # severity as a rate-limit breach would train whoever reads this
    # table to skim past the rows that matter.
    AuthAuditEvent.LOGIN_WRONG_PORTAL: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.INFO, WriteMode.SYNC),
    # A key being minted or killed is a permanent fact about a
    # supplier's integration, and the kind of thing that gets asked
    # about months later ("who turned our feed off?"). SYNC because
    # losing it to a dropped background thread would defeat the point.
    AuthAuditEvent.API_KEY_CREATED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuthAuditEvent.API_KEY_REVOKED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    # Repeated failures against the machine door are what a credential
    # guessing run looks like -- this is the row an investigator counts.
    AuthAuditEvent.API_KEY_AUTH_FAILED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    # Usually a misconfigured integration rather than an attack, so INFO
    # -- but still recorded, because it is also what a stolen key being
    # probed for reach looks like.
    AuthAuditEvent.API_KEY_SCOPE_DENIED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.INFO, WriteMode.SYNC),
}


def get_policy(event_name: AuditEventNameType) -> EventPolicy:
    return EVENT_POLICIES.get(event_name, DEFAULT_POLICY)
