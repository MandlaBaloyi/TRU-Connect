"""
Real-Postgres test for the cleanup job service, matching this project's
existing testing discipline (no mocking of the DB layer).

Rather than shrinking UNVERIFIED_EMAIL_CLEANUP_DAYS and waiting in real
time, rows are seeded with a backdated `created_at` directly — the job's
query only cares what the timestamp says, not how much wall-clock time
actually passed.

ADJUST ME: assumes fixtures `db_session` (a real, empty-per-test Postgres
session) and `make_user(...)` already exist in your test suite (or reuse
whatever convention tests/test_auth.py already established). This test
calls run() directly, inside whatever app-context fixture your suite
already provides for DB tests — it does not go through the scheduler.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.domains.auth.jobs.cleanup_unverified_emails import run as cleanup_unverified_emails
from src.domains.auth.models.user import User, VerificationStatus
from src.domains.security.rules.thresholds import UNVERIFIED_EMAIL_CLEANUP_DAYS


def _days_ago(days: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def test_deletes_only_unverified_emails_older_than_threshold(db_session, make_user):
    make_user(
        email="old-unverified@example.com",
        verification_status=VerificationStatus.UNVERIFIED,
        created_at=_days_ago(UNVERIFIED_EMAIL_CLEANUP_DAYS + 1),
    )
    make_user(
        email="recent-unverified@example.com",
        verification_status=VerificationStatus.UNVERIFIED,
        created_at=_days_ago(UNVERIFIED_EMAIL_CLEANUP_DAYS - 1),
    )
    make_user(
        email="old-verified@example.com",
        verification_status=VerificationStatus.VERIFIED,
        created_at=_days_ago(UNVERIFIED_EMAIL_CLEANUP_DAYS + 1),
    )
    db_session.commit()

    result = cleanup_unverified_emails()

    assert result.success is True
    assert result.count == 1

    remaining_emails = {u.email for u in db_session.query(User).all()}
    assert remaining_emails == {"recent-unverified@example.com", "old-verified@example.com"}


def test_idempotent_second_run_deletes_nothing(db_session, make_user):
    make_user(
        email="old-unverified@example.com",
        verification_status=VerificationStatus.UNVERIFIED,
        created_at=_days_ago(UNVERIFIED_EMAIL_CLEANUP_DAYS + 1),
    )
    db_session.commit()

    first = cleanup_unverified_emails()
    second = cleanup_unverified_emails()

    assert first.count == 1
    assert second.count == 0
    assert second.success is True
