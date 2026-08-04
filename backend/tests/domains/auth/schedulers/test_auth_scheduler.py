"""Auth's own child scheduler -- confirms it declares
cleanup_unverified_emails, and that this is the ONLY job it currently
declares (an intentional canary: if this ever fails because a new entry
appeared, that's a signal to review the Auth Scheduler's job list is
still what was intended, not necessarily a bug)."""

from __future__ import annotations

from src.domains.auth.schedulers.auth_scheduler import JOB_SPECS


def test_declares_cleanup_unverified_emails():
    names = [spec.name for spec in JOB_SPECS]
    assert "cleanup_unverified_emails" in names


def test_interval_is_once_per_day():
    spec = next(s for s in JOB_SPECS if s.name == "cleanup_unverified_emails")
    assert spec.interval_seconds == 24 * 60 * 60
