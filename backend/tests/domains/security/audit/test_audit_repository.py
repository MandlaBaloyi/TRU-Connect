"""
Repository behaviour against a real database, matching this project's
existing testing discipline (no mocking of the DB layer).

Focus is on the properties that are easy to get subtly wrong and painful
to discover in production: cursor pagination stability, aggregate
correctness, and timeline ordering.

ADJUST ME: assumes an `app`/`db_session` fixture pair providing a real
database and app context, matching whatever tests/test_auth.py already
established.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.domains.security.models.audit_event import AuditEventRecord
from src.domains.security.repositories.audit_repository import (
    AuditRepository,
    AuditSearchFilters,
)


def _event(**overrides) -> AuditEventRecord:
    defaults = dict(
        id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        domain="auth",
        module="auth_service",
        event_name="auth.login_failed",
        category="authentication",
        severity="medium",
        status="failure",
        actor_type="user",
        email="a@example.com",
        ip_address="198.51.100.7",
        event_metadata={},
    )
    defaults.update(overrides)
    return AuditEventRecord(**defaults)


def test_insert_and_search_roundtrip(db_session):
    AuditRepository.insert(_event(email="round@example.com"))
    page = AuditRepository.search(AuditSearchFilters(email="round@example.com"))
    assert len(page.items) == 1


def test_search_returns_newest_first(db_session):
    now = datetime.now(timezone.utc)
    AuditRepository.insert(_event(email="a@x.com", timestamp=now - timedelta(hours=2)))
    AuditRepository.insert(_event(email="a@x.com", timestamp=now - timedelta(hours=1)))
    AuditRepository.insert(_event(email="a@x.com", timestamp=now))

    page = AuditRepository.search(AuditSearchFilters(email="a@x.com"))
    timestamps = [i.timestamp for i in page.items]
    assert timestamps == sorted(timestamps, reverse=True)


def test_cursor_pagination_does_not_skip_or_repeat(db_session):
    now = datetime.now(timezone.utc)
    for i in range(10):
        AuditRepository.insert(_event(email="page@x.com", timestamp=now - timedelta(minutes=i)))

    first = AuditRepository.search(AuditSearchFilters(email="page@x.com"), limit=4)
    assert first.has_more is True
    second = AuditRepository.search(
        AuditSearchFilters(email="page@x.com"), limit=4, cursor=first.next_cursor
    )

    first_ids = {i.id for i in first.items}
    second_ids = {i.id for i in second.items}
    assert first_ids.isdisjoint(second_ids), "pagination repeated a row"
    assert len(first.items) == 4 and len(second.items) == 4


def test_cursor_pagination_is_stable_with_identical_timestamps(db_session):
    """
    Many events can share a timestamp under load. Paginating on timestamp
    alone would drop or duplicate rows at the boundary — the id tiebreaker
    is what prevents it.
    """
    same_time = datetime.now(timezone.utc)
    for _ in range(6):
        AuditRepository.insert(_event(email="tie@x.com", timestamp=same_time))

    first = AuditRepository.search(AuditSearchFilters(email="tie@x.com"), limit=3)
    second = AuditRepository.search(
        AuditSearchFilters(email="tie@x.com"), limit=3, cursor=first.next_cursor
    )

    assert {i.id for i in first.items}.isdisjoint({i.id for i in second.items})


def test_search_limit_is_capped(db_session):
    page = AuditRepository.search(limit=99999)
    assert len(page.items) <= 500


def test_get_by_correlation_returns_flow_in_forward_order(db_session):
    corr = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    AuditRepository.insert(_event(event_name="auth.otp_verified", correlation_id=corr, timestamp=now))
    AuditRepository.insert(_event(event_name="auth.otp_created", correlation_id=corr, timestamp=now - timedelta(seconds=30)))

    flow = AuditRepository.get_by_correlation(corr)
    assert [e.event_name for e in flow] == ["auth.otp_created", "auth.otp_verified"]


def test_count_failed_logins_by_ip(db_session):
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    for _ in range(3):
        AuditRepository.insert(_event(ip_address="203.0.113.1", event_name="auth.login_failed"))
    AuditRepository.insert(_event(ip_address="203.0.113.2", event_name="auth.login_failed"))

    results = dict(AuditRepository.count_failed_logins_by_ip(since=since))
    assert results["203.0.113.1"] == 3
    assert results["203.0.113.2"] == 1


def test_count_by_event(db_session):
    AuditRepository.insert(_event(event_name="auth.login_failed"))
    AuditRepository.insert(_event(event_name="auth.login_failed"))
    AuditRepository.insert(_event(event_name="auth.login_success", status="success"))

    counts = AuditRepository.count_by_event()
    assert counts["auth.login_failed"] == 2
    assert counts["auth.login_success"] == 1


def test_time_bucket_is_validated_against_allowlist(db_session):
    """The bucket value lands inside a SQL function call — it must not be
    free-form."""
    with pytest.raises(ValueError):
        AuditRepository.count_events_over_time(
            since=datetime.now(timezone.utc), bucket="hour; DROP TABLE users",
        )


def test_filters_combine(db_session):
    AuditRepository.insert(_event(email="combo@x.com", ip_address="1.1.1.1", status="failure"))
    AuditRepository.insert(_event(email="combo@x.com", ip_address="2.2.2.2", status="failure"))

    page = AuditRepository.search(
        AuditSearchFilters(email="combo@x.com", ip_address="1.1.1.1")
    )
    assert len(page.items) == 1
