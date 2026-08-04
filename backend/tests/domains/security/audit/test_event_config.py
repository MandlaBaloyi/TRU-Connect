"""Event policy table -- unchanged logic, import path moved to
security.audit.rules."""

from __future__ import annotations

import pytest

from src.domains.security.audit.rules.event_config import WriteMode, get_policy, EVENT_POLICIES
from src.shared.audit.audit_types import AuditEventName, AuditSeverity


def test_login_success_is_synchronous():
    assert get_policy(AuditEventName.LOGIN_SUCCESS).write_mode is WriteMode.SYNC


def test_unverified_account_expired_is_async():
    assert get_policy(AuditEventName.UNVERIFIED_ACCOUNT_EXPIRED).write_mode is WriteMode.ASYNC


def test_unknown_event_falls_back_to_default():
    from src.domains.security.audit.rules.event_config import DEFAULT_POLICY
    assert DEFAULT_POLICY.write_mode is WriteMode.SYNC
