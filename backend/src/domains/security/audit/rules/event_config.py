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
}


def get_policy(event_name: AuditEventName) -> EventPolicy:
    return EVENT_POLICIES.get(event_name, DEFAULT_POLICY)
