"""
Per-event policy: category, severity, and write mode.

Centralized here rather than scattered across publishers so that "how
seriously do we take this event" is one table you can read top-to-bottom
and change in a diff — the same discipline already applied to
thresholds.py.

WRITE MODE — the approved hybrid policy:

  SYNC  : written inside the request, before the response returns. Used
          for events that must never be lost to a queue failure, because
          they are the evidence an investigation depends on. Costs one
          extra INSERT on the request path; acceptable for low-frequency
          security-critical events.

  ASYNC : handed to shared/queue.py and written by a background worker.
          Used for high-volume routine events where losing one on a hard
          crash is tolerable and request latency matters more.

Today shared/queue.py runs an in-process background worker, so ASYNC
means "off the request thread." When Redis/Celery is introduced later,
ASYNC transparently becomes a real distributed queue with no change to
any publisher or to this table — that indirection is the entire point of
routing through the existing queue abstraction rather than spawning
threads here.
"""

from __future__ import annotations

import enum
from typing import NamedTuple

from src.shared.audit_types import AuditCategory, AuditEventName, AuditSeverity


class WriteMode(str, enum.Enum):
    SYNC = "sync"
    ASYNC = "async"


class EventPolicy(NamedTuple):
    category: AuditCategory
    severity: AuditSeverity
    write_mode: WriteMode


# Fallback for any event not explicitly listed below — deliberately
# conservative (sync, medium) so a newly-added event is never silently
# treated as low-value. Tighten it to ASYNC explicitly once you know it's
# high-volume and non-critical.
DEFAULT_POLICY = EventPolicy(
    category=AuditCategory.SYSTEM,
    severity=AuditSeverity.INFO,
    write_mode=WriteMode.SYNC,
)

_AUTH = AuditCategory.AUTHENTICATION
_ACCOUNT = AuditCategory.ACCOUNT_MANAGEMENT
_SYSTEM = AuditCategory.SYSTEM

_INFO = AuditSeverity.INFO
_LOW = AuditSeverity.LOW
_MED = AuditSeverity.MEDIUM
_HIGH = AuditSeverity.HIGH
_CRIT = AuditSeverity.CRITICAL

SYNC = WriteMode.SYNC
ASYNC = WriteMode.ASYNC


EVENT_POLICIES: dict[AuditEventName, EventPolicy] = {
    # --- Registration: success/failure are critical evidence; the
    #     intermediate "requested" step is routine. ---
    AuditEventName.REGISTER_REQUESTED:        EventPolicy(_AUTH, _INFO, ASYNC),
    AuditEventName.REGISTER_SUCCESS:          EventPolicy(_AUTH, _LOW,  SYNC),
    AuditEventName.REGISTER_FAILED:           EventPolicy(_AUTH, _MED,  SYNC),
    AuditEventName.REGISTER_ROLE_CONFLICT:    EventPolicy(_AUTH, _MED,  SYNC),
    AuditEventName.REGISTER_RESUMED:          EventPolicy(_AUTH, _INFO, ASYNC),

    # --- Email verification ---
    AuditEventName.EMAIL_VERIFICATION_SENT:   EventPolicy(_AUTH, _INFO, ASYNC),
    AuditEventName.EMAIL_VERIFIED:            EventPolicy(_AUTH, _LOW,  SYNC),
    AuditEventName.EMAIL_VERIFICATION_FAILED: EventPolicy(_AUTH, _MED,  SYNC),
    AuditEventName.EMAIL_VERIFICATION_EXPIRED:EventPolicy(_AUTH, _INFO, ASYNC),

    # --- OTP: high volume. Only failures carry attack signal, so only
    #     failures are sync. ---
    AuditEventName.OTP_CREATED:               EventPolicy(_AUTH, _INFO, ASYNC),
    AuditEventName.OTP_SENT:                  EventPolicy(_AUTH, _INFO, ASYNC),
    AuditEventName.OTP_VERIFIED:              EventPolicy(_AUTH, _LOW,  ASYNC),
    AuditEventName.OTP_FAILED:                EventPolicy(_AUTH, _MED,  SYNC),
    AuditEventName.OTP_RESENT:                EventPolicy(_AUTH, _INFO, ASYNC),
    AuditEventName.OTP_EXPIRED:               EventPolicy(_AUTH, _INFO, ASYNC),

    # --- Login: the core of any brute-force investigation. All sync
    #     except the plain success case's volume twin. ---
    AuditEventName.LOGIN_SUCCESS:             EventPolicy(_AUTH, _LOW,  SYNC),
    AuditEventName.LOGIN_FAILED:              EventPolicy(_AUTH, _MED,  SYNC),
    AuditEventName.LOGIN_BLOCKED:             EventPolicy(_AUTH, _HIGH, SYNC),
    AuditEventName.LOGIN_LOCKED:              EventPolicy(_AUTH, _HIGH, SYNC),
    AuditEventName.LOGIN_RATE_LIMITED:        EventPolicy(_AUTH, _MED,  SYNC),
    AuditEventName.LOGIN_UNVERIFIED:          EventPolicy(_AUTH, _LOW,  ASYNC),

    # --- Password reset: account-takeover pathway. Treated seriously. ---
    AuditEventName.PASSWORD_RESET_REQUESTED:  EventPolicy(_AUTH, _MED,  SYNC),
    AuditEventName.PASSWORD_RESET_TOKEN_CREATED: EventPolicy(_AUTH, _MED, ASYNC),
    AuditEventName.PASSWORD_RESET_SUCCESS:    EventPolicy(_AUTH, _HIGH, SYNC),
    AuditEventName.PASSWORD_RESET_FAILED:     EventPolicy(_AUTH, _MED,  SYNC),
    AuditEventName.PASSWORD_RESET_EXPIRED:    EventPolicy(_AUTH, _INFO, ASYNC),

    # --- Tokens: very high volume (every refresh). Routine. ---
    AuditEventName.TOKEN_CREATED:             EventPolicy(_AUTH, _INFO, ASYNC),
    AuditEventName.TOKEN_REFRESHED:           EventPolicy(_AUTH, _INFO, ASYNC),
    AuditEventName.TOKEN_REVOKED:             EventPolicy(_AUTH, _LOW,  ASYNC),
    AuditEventName.TOKEN_EXPIRED:             EventPolicy(_AUTH, _INFO, ASYNC),

    # --- Logout ---
    AuditEventName.LOGOUT:                    EventPolicy(_AUTH, _INFO, ASYNC),
    AuditEventName.LOGOUT_ALL_DEVICES:        EventPolicy(_AUTH, _MED,  SYNC),

    # --- Account administration: rare, irreversible, always sync. ---
    AuditEventName.ACCOUNT_ENABLED:           EventPolicy(_ACCOUNT, _HIGH, SYNC),
    AuditEventName.ACCOUNT_DISABLED:          EventPolicy(_ACCOUNT, _HIGH, SYNC),
    AuditEventName.ACCOUNT_DELETED:           EventPolicy(_ACCOUNT, _CRIT, SYNC),
    AuditEventName.ACCOUNT_UNLOCKED:          EventPolicy(_ACCOUNT, _HIGH, SYNC),
    AuditEventName.ROLE_CHANGED:              EventPolicy(_ACCOUNT, _CRIT, SYNC),
    AuditEventName.PERMISSION_CHANGED:        EventPolicy(_ACCOUNT, _CRIT, SYNC),

    # --- Platform / system ---
    AuditEventName.UNVERIFIED_ACCOUNT_EXPIRED: EventPolicy(_SYSTEM, _INFO, ASYNC),
    AuditEventName.SCHEDULED_JOB_COMPLETED:    EventPolicy(_SYSTEM, _INFO, ASYNC),
    AuditEventName.SCHEDULED_JOB_FAILED:       EventPolicy(_SYSTEM, _HIGH, SYNC),
}


def get_policy(event_name: AuditEventName) -> EventPolicy:
    return EVENT_POLICIES.get(event_name, DEFAULT_POLICY)
