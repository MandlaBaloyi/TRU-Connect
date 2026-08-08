"""
Per-event policy: category, severity, and write mode. Relocated from
security/rules/ to security/audit/rules/ -- this is audit-specific
policy, distinct from security/rules/thresholds.py (a general Auth
threshold), which correctly stays where it is.
"""

from __future__ import annotations

import enum
from typing import NamedTuple

from src.shared.audit.audit_types import AuditCategory, AuditEventName, AuditSeverity


class WriteMode(str, enum.Enum):
    SYNC = "sync"
    ASYNC = "async"


class EventPolicy(NamedTuple):
    category: AuditCategory
    severity: AuditSeverity
    write_mode: WriteMode


DEFAULT_POLICY = EventPolicy(AuditCategory.SYSTEM, AuditSeverity.INFO, WriteMode.SYNC)

EVENT_POLICIES: dict[AuditEventName, EventPolicy] = {
    AuditEventName.LOGIN_SUCCESS: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuditEventName.UNVERIFIED_ACCOUNT_EXPIRED: EventPolicy(AuditCategory.SYSTEM, AuditSeverity.INFO, WriteMode.ASYNC),
    # Rate-limit violations -- AUTHENTICATION category (every Phase 1
    # limited route is an auth route) and MEDIUM severity: a real
    # signal worth an investigator's attention, but on its own not yet
    # the CRITICAL-tier event a confirmed account compromise would be.
    AuditEventName.LOGIN_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuditEventName.REGISTER_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuditEventName.REFRESH_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuditEventName.PASSWORD_RESET_REQUEST_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuditEventName.PASSWORD_RESET_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuditEventName.OTP_REQUEST_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
    AuditEventName.OTP_VERIFY_RATE_LIMITED: EventPolicy(AuditCategory.AUTHENTICATION, AuditSeverity.MEDIUM, WriteMode.SYNC),
}


def get_policy(event_name: AuditEventName) -> EventPolicy:
    return EVENT_POLICIES.get(event_name, DEFAULT_POLICY)
