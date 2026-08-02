"""
Safe execution wrapper + observer hook.

Every job registered through registry.py is wrapped by make_safe() before
being handed to the engine — this guarantees uniform logging, timing, and
exception isolation for every job regardless of which engine ultimately
calls it (APScheduler today, Celery tomorrow): log start, log finish,
measure duration, catch exceptions, never crash the scheduler.

Also owns a tiny observer list: after each execution attempt, every
registered listener is called with a JobExecutionOutcome. This is how
security/schedulers/monitor.py gets execution data without Platform ever
importing Security — Security subscribes to Platform by calling
add_listener(), Platform never reaches toward Security.
"""

from __future__ import annotations

import logging
import time
from contextlib import nullcontext
from datetime import datetime, timezone
from typing import Callable, ContextManager, Optional

from src.shared.scheduling_types import JobExecutionOutcome, JobResult

logger = logging.getLogger(__name__)

_listeners: list[Callable[[JobExecutionOutcome], None]] = []


def add_listener(callback: Callable[[JobExecutionOutcome], None]) -> None:
    """Register a callback invoked after every job execution attempt
    (success, business-logic failure, or raised exception). Used by
    security/schedulers/monitor.py to build health/history views without
    Platform depending on Security."""
    _listeners.append(callback)


def _notify(outcome: JobExecutionOutcome) -> None:
    for listener in _listeners:
        try:
            listener(outcome)
        except Exception:  # noqa: BLE001 — a broken listener must never break job execution
            logger.exception("scheduler runner: listener raised for job '%s'", outcome.job_name)


def make_safe(
    job_name: str,
    func: Callable[[], JobResult],
    context_factory: Optional[Callable[[], ContextManager]] = None,
) -> Callable[[], None]:
    """
    Wrap a domain job-service function (e.g.
    auth.jobs.cleanup_unverified_emails.run) into a zero-argument callable
    safe to hand to any scheduling engine.

    `context_factory`, if given, is called fresh on every execution to
    produce a context manager to run inside — e.g.
    `lambda: app.app_context()` for Flask-SQLAlchemy's context-bound
    db.session. Kept generic and optional so this module has no Flask
    dependency of its own; trigger.py is the only place that supplies a
    Flask-specific context_factory.
    """

    def _wrapped() -> None:
        started_at = datetime.now(timezone.utc)
        start = time.monotonic()
        ctx = context_factory() if context_factory is not None else nullcontext()
        try:
            with ctx:
                result = func()
            if not isinstance(result, JobResult):
                # A job that forgets to return a JobResult is a bug in that
                # job, not something that should crash the scheduler — but
                # it IS worth surfacing loudly, since silent bad returns
                # defeat the whole point of monitoring having something
                # meaningful to show.
                raise TypeError(f"Job '{job_name}' must return a JobResult, got {type(result)!r}")
            duration_ms = (time.monotonic() - start) * 1000
            logger.info(
                "job '%s' finished success=%s count=%s duration_ms=%.1f",
                job_name, result.success, result.count, duration_ms,
            )
            _notify(JobExecutionOutcome(
                job_name=job_name,
                started_at=started_at,
                duration_ms=duration_ms,
                success=result.success,
                result=result,
            ))
        except Exception as exc:  # noqa: BLE001 — intentional: isolate any job failure
            duration_ms = (time.monotonic() - start) * 1000
            logger.exception("job '%s' raised an exception", job_name)
            _notify(JobExecutionOutcome(
                job_name=job_name,
                started_at=started_at,
                duration_ms=duration_ms,
                success=False,
                error=str(exc),
            ))

    return _wrapped
