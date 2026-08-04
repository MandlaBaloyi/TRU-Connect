"""
Security's monitoring layer — proves it correctly aggregates
JobExecutionOutcome events into per-job health without owning any
scheduling engine or timer itself. Feeds outcomes directly (not through a
real scheduler run) since monitor.py's only real job is aggregation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domains.security.schedulers import monitor
from src.shared.scheduling.scheduling_types import JobExecutionOutcome, JobResult


@pytest.fixture(autouse=True)
def _reset_monitor_state():
    monitor._reset_for_tests()
    yield
    monitor._reset_for_tests()


def _outcome(name, success, started_at=None, error=None, count=0):
    return JobExecutionOutcome(
        job_name=name,
        started_at=started_at or datetime.now(timezone.utc),
        duration_ms=10.0,
        success=success,
        result=JobResult(success=success, count=count) if success else None,
        error=error,
    )


def test_records_success_and_failure_counts():
    monitor.on_job_executed(_outcome("job_a", True, count=5))
    monitor.on_job_executed(_outcome("job_a", False, error="db down"))

    health = monitor.get_job_health("job_a")[0]
    assert health.run_count == 2
    assert health.failure_count == 1
    assert health.last_success is False
    assert health.last_error == "db down"


def test_get_job_health_all_jobs():
    monitor.on_job_executed(_outcome("job_a", True))
    monitor.on_job_executed(_outcome("job_b", True))

    names = {h.job_name for h in monitor.get_job_health()}
    assert names == {"job_a", "job_b"}


def test_history_is_bounded():
    for _ in range(monitor._MAX_HISTORY_PER_JOB + 10):
        monitor.on_job_executed(_outcome("job_a", True))
    health = monitor.get_job_health("job_a")[0]
    assert len(health.history) == monitor._MAX_HISTORY_PER_JOB


def test_detect_missed_jobs_flags_stale_and_never_run():
    stale_time = datetime.now(timezone.utc) - timedelta(hours=10)
    monitor.on_job_executed(_outcome("job_a", True, started_at=stale_time))
    # job_b never runs at all

    missed = monitor.detect_missed_jobs({"job_a": 3600, "job_b": 3600}, grace_multiplier=2.0)
    assert "job_a" in missed
    assert "job_b" in missed


def test_detect_missed_jobs_does_not_flag_recent_runs():
    monitor.on_job_executed(_outcome("job_a", True))
    missed = monitor.detect_missed_jobs({"job_a": 3600}, grace_multiplier=2.0)
    assert "job_a" not in missed
