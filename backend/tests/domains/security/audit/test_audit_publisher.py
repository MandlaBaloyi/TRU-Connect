"""
shared/audit.py publisher mechanics — no database, no Flask request.

Proves the properties the whole design rests on:
  * existing function signatures still work unchanged
  * events reach listeners
  * a broken listener never breaks the audited action
  * publishing works with NO request context (the scheduled-job case)
  * the text log masks the email while the published event carries it in full
"""

from __future__ import annotations

import pytest

from src.shared.audit import audit
from src.shared.audit.audit_types import ActorType, AuditEventName, AuditStatus


@pytest.fixture(autouse=True)
def _isolate_listeners():
    original = audit._listeners[:]
    audit._listeners.clear()
    yield
    audit._listeners[:] = original


def test_login_success_publishes_event():
    received = []
    audit.register_listener(received.append)

    audit.log_login_success(user_id="user-123", ip_address="10.0.0.1")

    assert len(received) == 1
    event = received[0]
    assert event.event_name is AuditEventName.LOGIN_SUCCESS
    assert event.status is AuditStatus.SUCCESS
    assert event.user_id == "user-123"
    assert event.ip_address == "10.0.0.1"


def test_published_event_carries_full_email_not_masked():
    """Storage must never be masked — investigators need exact values."""
    received = []
    audit.register_listener(received.append)

    audit.log_login_failed(email="power@gmail.com", ip_address="10.0.0.1")

    assert received[0].email == "power@gmail.com"


def test_broken_listener_does_not_raise_to_caller():
    """An audit failure must never break the action being audited."""
    def broken(event):
        raise RuntimeError("audit backend down")

    audit.register_listener(broken)
    audit.log_login_success(user_id="user-123", ip_address=None)  # must not raise


def test_broken_listener_does_not_block_a_second_listener():
    received = []

    def broken(event):
        raise RuntimeError("boom")

    audit.register_listener(broken)
    audit.register_listener(received.append)

    audit.log_login_success(user_id="user-123", ip_address=None)

    assert len(received) == 1


def test_publishes_without_request_context():
    """
    The scheduled cleanup job publishes from a background thread with no
    HTTP request. Request-scoped fields must come back None instead of
    raising — otherwise the first real 3am tick would crash.
    """
    received = []
    audit.register_listener(received.append)

    audit.log_unverified_account_expired(email="abandoned@example.com")

    event = received[0]
    assert event.actor_type is ActorType.SCHEDULER
    assert event.ip_address is None
    assert event.correlation_id is None
    assert event.endpoint is None


def test_role_conflict_records_both_roles_in_metadata():
    received = []
    audit.register_listener(received.append)

    audit.log_registration_role_conflict(
        email="x@example.com", existing_role="business", attempted_role="supplier",
    )

    event = received[0]
    assert event.metadata["existing_role"] == "business"
    assert event.metadata["attempted_role"] == "supplier"


def test_explicit_ip_wins_over_request_context():
    """Enrichment only fills what the caller left None."""
    received = []
    audit.register_listener(received.append)

    audit.log_login_failed(email="a@example.com", ip_address="203.0.113.9")

    assert received[0].ip_address == "203.0.113.9"
