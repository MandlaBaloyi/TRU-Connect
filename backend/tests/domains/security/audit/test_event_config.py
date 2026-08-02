"""
Event policy table — proves the approved hybrid write policy is actually
encoded, not just described in a docstring.
"""

from __future__ import annotations

import pytest

from src.domains.security.rules.event_config import WriteMode, get_policy
from src.shared.audit_types import AuditEventName, AuditSeverity


CRITICAL_SYNC_EVENTS = [
    AuditEventName.LOGIN_FAILED,
    AuditEventName.LOGIN_SUCCESS,
    AuditEventName.LOGIN_LOCKED,
    AuditEventName.PASSWORD_RESET_SUCCESS,
    AuditEventName.PASSWORD_RESET_REQUESTED,
    AuditEventName.REGISTER_SUCCESS,
    AuditEventName.ACCOUNT_DISABLED,
    AuditEventName.ACCOUNT_DELETED,
]


@pytest.mark.parametrize("event", CRITICAL_SYNC_EVENTS)
def test_approved_critical_events_are_synchronous(event):
    """These must never be lost to a queue failure."""
    assert get_policy(event).write_mode is WriteMode.SYNC


@pytest.mark.parametrize("event", [
    AuditEventName.TOKEN_REFRESHED,
    AuditEventName.OTP_SENT,
    AuditEventName.LOGOUT,
])
def test_high_volume_routine_events_are_async(event):
    assert get_policy(event).write_mode is WriteMode.ASYNC


def test_every_event_name_has_a_policy():
    """
    A missing policy silently falls back to DEFAULT_POLICY, which would
    misclassify a new event rather than failing loudly. Catch it here.
    """
    from src.domains.security.rules.event_config import EVENT_POLICIES
    missing = [e.name for e in AuditEventName if e not in EVENT_POLICIES]
    assert missing == [], f"Events without an explicit policy: {missing}"


def test_account_deletion_is_critical_severity():
    assert get_policy(AuditEventName.ACCOUNT_DELETED).severity is AuditSeverity.CRITICAL


def test_unknown_event_falls_back_to_conservative_default():
    from src.domains.security.rules.event_config import DEFAULT_POLICY
    assert DEFAULT_POLICY.write_mode is WriteMode.SYNC
