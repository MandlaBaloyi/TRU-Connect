"""Real APSchedulerEngine, minimal smoke test -- unchanged logic, only
the import path moved with the file (domains/platform/schedulers ->
master_scheduler)."""

from __future__ import annotations

import time

from src.master_scheduler.engine import APSchedulerEngine


def test_engine_starts_runs_and_stops():
    engine = APSchedulerEngine()
    calls = {"n": 0}
    engine.add_job("test_job", lambda: calls.__setitem__("n", calls["n"] + 1), interval_seconds=0.1)
    assert engine.is_running is False
    engine.start()
    assert engine.is_running is True
    time.sleep(0.35)
    engine.stop()
    assert engine.is_running is False
    assert calls["n"] >= 2


def test_start_is_idempotent():
    engine = APSchedulerEngine()
    engine.start()
    engine.start()
    assert engine.is_running is True
    engine.stop()
    engine.stop()
    assert engine.is_running is False
