"""
Scheduler interface -- the seam between the Master's registry/runner and
whatever concrete scheduling engine actually runs the clock (APScheduler
today; Celery, RQ, a cloud scheduler, or plain cron later).

Also home to JobSpec: the shape every domain's own scheduler file (e.g.
domains/auth/schedulers/auth_scheduler.py) constructs when it declares
its jobs. Defined HERE, not in registry.py, specifically so a domain's
scheduler file can import JobSpec without importing registry.py itself --
registry.py imports EVERY domain's scheduler file to collect their jobs,
so if JobSpec lived in registry.py, every domain file importing it back
would be a circular import. interfaces.py imports nothing domain-specific
and nothing from registry.py, so it's safe common ground.
"""

from __future__ import annotations

import abc
from typing import Callable, NamedTuple

from src.shared.scheduling.scheduling_types import JobResult


class JobSpec(NamedTuple):
    """One scheduled job, as declared by the domain that owns its logic.
    `func` is the domain's plain job-service function (e.g.
    auth.jobs.cleanup_unverified_emails.run) -- it knows nothing about
    scheduling; only the domain's own scheduler file and this Spec know
    it's scheduled, and only registry.py decides how it actually runs."""
    name: str
    func: Callable[[], JobResult]
    interval_seconds: float


class SchedulerEngine(abc.ABC):
    """
    Minimal contract any concrete scheduling engine must satisfy.
    Deliberately small: just enough for registry.py to schedule work and
    trigger.py to start/stop it. No job-specific knowledge belongs here.
    """

    @abc.abstractmethod
    def add_job(self, job_id: str, func: Callable[[], None], interval_seconds: float) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_running(self) -> bool:
        raise NotImplementedError
