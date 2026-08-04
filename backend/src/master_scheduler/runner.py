"""
Safe execution wrapper + observer hook.

Every job the Master schedules is wrapped by make_safe() before being
handed to the engine -- uniform logging, timing, and exception isolation
for every job regardless of which domain declared it or which engine
ultimately calls it.

Also owns a tiny observer list: after each execution attempt, every
registered listener is called with a JobExecutionOutcome. This is how
security/schedulers/monitor.py gets execution data without the Master
ever importing Security -- Security subscribes by calling add_listener(),
the Master never reaches toward Security.
"""

from __future__ import annotations

import logging
import time
from contextlib import nullcontext
from datetime import datetime, timezone
from typing import Callable, ContextManager, Optional

from src.shared.scheduling.scheduling_types import JobExecutionOutcome, JobResult

logger = logging.getLogger(__name__)

_listeners: list[Callable[[JobExecutionOutcome], None]] = []


def add_listener(callback: Callable[[JobExecutionOutcome], None]) -> None:
    _listeners.append(callback)


def _notify(outcome: JobExecutionOutcome) -> None:
    for listener in _listeners:
        try:
            listener(outcome)
        except Exception:  # noqa: BLE001
            logger.exception("scheduler runner: listener raised for job '%s'", outcome.job_name)


def make_safe(
    job_name: str,
    func: Callable[[], JobResult],
    context_factory: Optional[Callable[[], ContextManager]] = None,
) -> Callable[[], None]:
    def _wrapped() -> None:
        started_at = datetime.now(timezone.utc)
        start = time.monotonic()
        ctx = context_factory() if context_factory is not None else nullcontext()
        try:
            with ctx:
                result = func()
            if not isinstance(result, JobResult):
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
        except Exception as exc:  # noqa: BLE001
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