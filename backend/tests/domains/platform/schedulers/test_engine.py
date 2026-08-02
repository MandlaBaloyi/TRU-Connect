"""
Real APSchedulerEngine, minimal smoke test — proves the engine actually
starts, runs a job, and stops, through the SchedulerEngine interface only
(no APScheduler-specific API used directly, matching how the rest of the
codebase is meant to interact with it).
"""

from __future__ import annotations

import time

from src.domains.platform.schedulers.engine import APSchedulerEngine


def test_engine_starts_runs_and_stops():
    engine = APSchedulerEngine()
    calls = {"n": 0}

    engine.add_job("test_job", lambda: calls.__setitem__("n", calls["n"] + 1), interval_seconds=0.1)
    assert engine.is_running is False

    engine.start()
    assert engine.is_running is True

    time.sleep(0.35)  # allow a couple of ticks
    engine.stop()

    assert engine.is_running is False
    assert calls["n"] >= 2


def test_start_is_idempotent():
    engine = APSchedulerEngine()
    engine.start()
    engine.start()  # must not raise
    assert engine.is_running is True
    engine.stop()
    engine.stop()  # must not raise
    assert engine.is_running is False
