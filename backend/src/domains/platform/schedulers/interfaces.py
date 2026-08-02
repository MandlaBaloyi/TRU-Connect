"""
Scheduler interface — the seam between Platform's registry/runner and
whatever concrete scheduling engine actually runs the clock (APScheduler
today; Celery, RQ, Kubernetes CronJobs, a cloud scheduler, or plain cron
later). Every other file in this codebase talks to THIS contract, never to
a concrete engine directly.

Swapping the engine later means writing a new class in (or alongside)
engine.py that implements SchedulerEngine, and changing one line in
trigger.py. Nothing in Auth, Business, Supplier, Verification, or Security
changes, because none of them import a concrete engine — they only ever
see this interface (indirectly, through registry.py/trigger.py) or plain
Python functions.
"""

from __future__ import annotations

import abc
from typing import Callable


class SchedulerEngine(abc.ABC):
    """
    Minimal contract any concrete scheduling engine must satisfy.
    Deliberately small: just enough for registry.py to schedule work and
    trigger.py to start/stop it. No job-specific knowledge belongs here.
    """

    @abc.abstractmethod
    def add_job(self, job_id: str, func: Callable[[], None], interval_seconds: float) -> None:
        """
        Schedule `func` (a zero-argument callable, already wrapped safe by
        runner.make_safe()) to run every `interval_seconds`, identified by
        `job_id`. Implementations should treat re-adding the same job_id as
        a replace, not a duplicate/error.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def start(self) -> None:
        """Start ticking. Safe to call on an already-started engine (no-op)."""
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self) -> None:
        """Stop ticking. Safe to call on an already-stopped engine (no-op)."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_running(self) -> bool:
        raise NotImplementedError
