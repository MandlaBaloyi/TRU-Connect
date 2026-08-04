"""
The ONLY file in this codebase allowed to import apscheduler.

Owns exactly one thing: a running APScheduler instance behind the
SchedulerEngine interface. Contains no job-specific knowledge, no
business logic, and no Flask-context handling (trigger.py supplies that
via runner.make_safe()'s context_factory parameter).

To swap APScheduler for Celery later: write a CeleryEngine class
implementing SchedulerEngine (here, or in a new engine_celery.py), and
change one line in trigger.py. Nothing else in the codebase changes.
"""

from __future__ import annotations

import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler

from src.master_scheduler.interfaces import SchedulerEngine

logger = logging.getLogger(__name__)


class APSchedulerEngine(SchedulerEngine):
    """APScheduler-backed implementation of SchedulerEngine."""

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler(daemon=True)

    def add_job(self, job_id: str, func: Callable[[], None], interval_seconds: float) -> None:
        self._scheduler.add_job(
            func,
            "interval",
            seconds=interval_seconds,
            id=job_id,
            replace_existing=True,
            max_instances=1,
        )
        logger.info("master scheduler: registered job '%s' every %ss", job_id, interval_seconds)

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("master scheduler: engine started")

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("master scheduler: engine stopped")

    @property
    def is_running(self) -> bool:
        return self._scheduler.running
