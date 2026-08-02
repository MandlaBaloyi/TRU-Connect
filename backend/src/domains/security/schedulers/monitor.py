"""
Monitoring layer for scheduled jobs — job health, execution history,
failure tracking, best-effort missed-execution detection.

This file owns NO scheduling engine, NO timer, and NO apscheduler import.
It only consumes JobExecutionOutcome events published by
platform.schedulers.runner — Security depends on Platform, never the
other way around. Platform's runner.py has no idea this file exists.

In-memory for now, same reasoning applied elsewhere in this project: a
single process is fine for MVP. If this needs to survive restarts or be
queried across multiple worker processes later, that is the trigger to add
a persistence table — not before.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.domains.platform.schedulers import runner
from src.shared.scheduling_types import JobExecutionOutcome

logger = logging.getLogger(__name__)


@dataclass
class JobHealth:
    """Read-facing rollup for a single job — shaped for eventual admin-panel
    consumption, same spirit as the earlier JobStatusView design."""
    job_name: str
    run_count: int = 0
    failure_count: int = 0
    last_run_at: Optional[datetime] = None
    last_success: Optional[bool] = None
    last_duration_ms: Optional[float] = None
    last_error: Optional[str] = None
    last_result_count: Optional[int] = None
    last_result_detail: Optional[str] = None
    history: list = field(default_factory=list)  # list[JobExecutionOutcome], bounded below


_lock = threading.RLock()
_health: dict[str, JobHealth] = {}
_MAX_HISTORY_PER_JOB = 50  # bounded so this never grows unbounded in memory


def on_job_executed(outcome: JobExecutionOutcome) -> None:
    """Listener callback — registered with runner.add_listener() below."""
    with _lock:
        health = _health.setdefault(outcome.job_name, JobHealth(job_name=outcome.job_name))
        health.run_count += 1
        if not outcome.success:
            health.failure_count += 1
            logger.warning("security monitor: job '%s' failed — %s", outcome.job_name, outcome.error)
        health.last_run_at = outcome.started_at
        health.last_success = outcome.success
        health.last_duration_ms = outcome.duration_ms
        health.last_error = outcome.error
        if outcome.result is not None:
            health.last_result_count = outcome.result.count
            health.last_result_detail = outcome.result.detail
        health.history.append(outcome)
        if len(health.history) > _MAX_HISTORY_PER_JOB:
            health.history.pop(0)


def get_job_health(job_name: Optional[str] = None) -> list[JobHealth]:
    """
    Read-only view, intended for a future admin API route. Permission-
    agnostic on purpose — RBAC/ABAC filtering (who can see what) belongs
    at the API layer, not here, matching the pattern already used
    elsewhere in this project.
    """
    with _lock:
        if job_name is not None:
            h = _health.get(job_name)
            return [h] if h else []
        return list(_health.values())


def detect_missed_jobs(expected_interval_seconds: dict, grace_multiplier: float = 2.0) -> list:
    """
    Best-effort check: returns names of jobs whose last run is older than
    (their expected interval * grace_multiplier), or that have never run
    despite being expected to.

    Not wired to any automatic alerting yet — call it on demand (e.g. from
    a future admin health-check route). Deliberately callable rather than
    self-scheduling, since Security must not own a timer of its own; if
    periodic alerting is ever wanted, that alert job would itself be
    registered through Platform's registry like any other scheduled job,
    with THIS function as its business logic — same "Platform owns when,
    a domain owns what" split applied recursively.
    """
    with _lock:
        now = datetime.now(timezone.utc)
        missed = []
        for name, interval in expected_interval_seconds.items():
            health = _health.get(name)
            if health is None or health.last_run_at is None:
                missed.append(name)
                continue
            grace = timedelta(seconds=interval * grace_multiplier)
            if (now - health.last_run_at) > grace:
                missed.append(name)
        return missed


def _reset_for_tests() -> None:
    """Not for production use — lets tests start from a clean state."""
    with _lock:
        _health.clear()


# Self-registers as a runner listener on import. This is the one place
# Security reaches toward Platform — Platform never imports Security.
runner.add_listener(on_job_executed)
