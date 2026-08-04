"""
Application startup hook. Starts the Master Scheduler exactly once.

Two things this guards against:
  1. Calling start() twice in the same process (accidental double-init).
  2. Flask's debug-mode reloader, which runs the app in TWO processes --
     without the guard below, both would start their own scheduler,
     silently double-executing every job.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from flask import Flask

from src.master_scheduler.engine import APSchedulerEngine
from src.master_scheduler.interfaces import SchedulerEngine
from src.master_scheduler.registry import register_all

logger = logging.getLogger(__name__)

_engine: Optional[SchedulerEngine] = None


def start(app: Flask) -> None:
    """
    Call once, from create_app(), AFTER db.init_app(app) and after all
    domain modules are otherwise importable -- right before `return app`.
    """
    global _engine

    if not _should_start_in_this_process(app):
        logger.info("master scheduler: skipping start in reloader watcher process")
        return

    if _engine is not None:
        logger.warning("master scheduler: start() called but already running -- ignoring")
        return

    # security.schedulers.monitor self-registers as a runner listener on
    # import -- imported here, not at this module's top level, so
    # Security only gets wired in at the moment the scheduler actually
    # starts, matching the same reasoning as before this file moved.
    import src.domains.security.schedulers.monitor  # noqa: F401

    _engine = APSchedulerEngine()
    register_all(_engine, context_factory=lambda: app.app_context())
    _engine.start()
    logger.info("master scheduler: started")


def stop() -> None:
    global _engine
    if _engine is not None:
        _engine.stop()
        _engine = None


def is_running() -> bool:
    return _engine is not None and _engine.is_running


def _should_start_in_this_process(app: Flask) -> bool:
    return (not app.debug) or os.environ.get("WERKZEUG_RUN_MAIN") == "true"
