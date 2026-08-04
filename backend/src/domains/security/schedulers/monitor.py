"""
Monitoring layer for scheduled jobs -- job health, bounded execution
history, and best-effort missed-execution detection.

This file owns NO scheduling engine, NO timer, and NO apscheduler
import. It only consumes JobExecutionOutcome events published by
src.master_scheduler.runner -- Security depends on the Master Scheduler,
never the other way around.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from src.master_scheduler import runner
from src.shared.scheduling.scheduling_types import JobExecutionOutcome

logger = logging.getLogger(__name__)

# How many recent executions to keep per job. Bounded deliberately --
# unbounded history on a daily job running for years would grow forever
# for no benefit; recent history is what actually matters for spotting
# a job that's started failing or gone quiet.
_MAX_HISTORY_PER_JOB = 50


@dataclass
class JobHealth:
    job_name: str
    run_count: int = 0
    failure_count: int = 0
    last_success: Optional[bool] = None
    last_error: Optional[str] = None
    last_run_at: Optional[datetime] = None
    history: List[JobExecutionOutcome] = field(default_factory=list)


_lock = threading.RLock()
_health: Dict[str, JobHealth] = {}


def on_job_executed(outcome: JobExecutionOutcome) -> None:
    with _lock:
        health = _health.setdefault(outcome.job_name, JobHealth(job_name=outcome.job_name))
        health.run_count += 1
        if not outcome.success:
            health.failure_count += 1
        health.last_success = outcome.success
        health.last_error = outcome.error
        health.last_run_at = outcome.started_at

        health.history.append(outcome)
        # Trim from the front so `history` always holds the MOST RECENT
        # _MAX_HISTORY_PER_JOB entries, not the oldest.
        if len(health.history) > _MAX_HISTORY_PER_JOB:
            del health.history[: len(health.history) - _MAX_HISTORY_PER_JOB]


def get_job_health(job_name: Optional[str] = None) -> List[JobHealth]:
    with _lock:
        if job_name is not None:
            health = _health.get(job_name)
            return [health] if health else []
        return list(_health.values())


def detect_missed_jobs(
    job_intervals: Dict[str, float],
    grace_multiplier: float = 1.5,
    now: Optional[datetime] = None,
) -> Set[str]:
    """
    Best-effort detection of jobs that should have run recently and
    haven't -- either they never ran at all, or their last run is older
    than `interval_seconds * grace_multiplier`.

    `grace_multiplier` exists because a job due every 3600s finishing at
    3601s isn't actually a problem -- only genuinely missed executions
    should be flagged, not ordinary scheduling jitter.
    """
    now = now or datetime.now(timezone.utc)
    missed: Set[str] = set()

    with _lock:
        for job_name, interval_seconds in job_intervals.items():
            health = _health.get(job_name)
            if health is None or health.last_run_at is None:
                missed.add(job_name)  # never run at all
                continue
            elapsed = (now - health.last_run_at).total_seconds()
            if elapsed > interval_seconds * grace_multiplier:
                missed.add(job_name)

    return missed


def _reset_for_tests() -> None:
    with _lock:
        _health.clear()


runner.add_listener(on_job_executed)