"""
Application startup hook. Starts the platform scheduler exactly once.

Two things this guards against:
  1. Calling start() twice in the same process (accidental double-init —
     e.g. a test suite importing create_app() more than once).
  2. Flask's debug-mode reloader, which runs the app in TWO processes (a
     parent "watcher" + the actual worker). Without the guard below, both
     processes would start their own scheduler, silently double-executing
     every job. This only shows up with debug=True (the default reloader
     is on whenever debug is on), which makes it an easy bug to miss in
     dev — logs look doubled, or row-cleanup counts look inconsistent,
     with no obvious cause.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from flask import Flask

from src.domains.platform.schedulers.engine import APSchedulerEngine
from src.domains.platform.schedulers.interfaces import SchedulerEngine
from src.domains.platform.schedulers.registry import register_all

logger = logging.getLogger(__name__)

_engine: Optional[SchedulerEngine] = None


def start(app: Flask) -> None:
    """
    Call once, from create_app(), AFTER db.init_app(app) and after all
    domain modules are otherwise importable — right before `return app`.

    Requires the Flask `app` instance because job services like
    cleanup_unverified_emails use db.session, which is Flask-context-bound.
    The scheduler engine runs jobs on its own thread, with no request to
    supply that context automatically — this wraps every job execution in
    `app.app_context()` via runner.make_safe()'s context_factory, so no
    individual job needs to know or care about this.
    """
    global _engine

    if not _should_start_in_this_process(app):
        logger.info("platform scheduler: skipping start in reloader watcher process")
        return

    if _engine is not None:
        logger.warning("platform scheduler: start() called but already running — ignoring")
        return

    # security.schedulers.monitor self-registers as a runner listener on
    # import — imported here (not at this module's top level) so Security
    # only gets wired in at the moment the scheduler actually starts,
    # making the coupling an explicit, intentional step rather than a side
    # effect of this module merely existing / being imported for its types.
    import src.domains.security.schedulers.monitor  # noqa: F401

    _engine = APSchedulerEngine()
    register_all(_engine, context_factory=lambda: app.app_context())
    _engine.start()
    logger.info("platform scheduler: started")


def stop() -> None:
    """Stop the engine. Mainly useful for clean test teardown."""
    global _engine
    if _engine is not None:
        _engine.stop()
        _engine = None


def is_running() -> bool:
    return _engine is not None and _engine.is_running


def _should_start_in_this_process(app: Flask) -> bool:
    """
    True unless we're in the parent "watcher" process spawned by
    Werkzeug's debug-mode auto-reloader (the process that never actually
    serves requests). Standard Flask/Werkzeug idiom: start unless we're in
    debug mode AND this isn't the reloaded child process.

    Known limitation: if debug=True is ever combined with
    use_reloader=False, this idiom would incorrectly skip starting
    (WERKZEUG_RUN_MAIN is only ever set by the reloader itself). Not a
    concern today since the reloader is left at its default (on) in dev —
    flagged here in case that ever changes.
    """
    return (not app.debug) or os.environ.get("WERKZEUG_RUN_MAIN") == "true"
