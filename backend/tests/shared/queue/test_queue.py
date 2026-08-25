"""
Tests for the background job queue -- formalizes the direct manual
proof already run before this file existed: real concurrency, and a
genuine, working ceiling on it.

REAL BUG FOUND DURING REVIEW: this used to be a single worker thread
processing one job at a time -- two suppliers submitting bulk imports
even a second apart meant the second one waited for the first one's
ENTIRE job to finish first. These tests exist specifically to prevent
that regression from silently coming back.
"""
from __future__ import annotations

import time

import pytest

from src.shared.queue import queue


@pytest.fixture(autouse=True)
def _reset_executor():
    """Each test gets its own fresh pool -- a prior test's executor
    persisting into the next would make timing assertions unreliable."""
    queue._executor = None
    queue._pending_count = 0
    yield
    queue._executor = None
    queue._pending_count = 0


def test_jobs_run_genuinely_concurrently_not_sequentially():
    results = []

    def slow_job(n):
        time.sleep(0.3)
        results.append(n)

    start = time.monotonic()
    for i in range(5):
        queue.enqueue(lambda n=i: slow_job(n))
    queue.wait_until_idle(timeout=5)
    elapsed = time.monotonic() - start

    assert sorted(results) == [0, 1, 2, 3, 4]
    # Would take ~1.5s if still sequential (the real bug this fixes) --
    # genuinely concurrent finishes in ~0.3s. 1.0s leaves real margin
    # for CI slowness without letting a real regression pass silently.
    assert elapsed < 1.0, f"jobs took {elapsed:.2f}s -- looks sequential, not concurrent"


def test_pool_is_genuinely_bounded_not_unlimited(monkeypatch):
    monkeypatch.setattr(queue, "MAX_WORKERS", 5)
    results = []

    def slow_job(n):
        time.sleep(0.3)
        results.append(n)

    start = time.monotonic()
    for i in range(10):  # double the pool size
        queue.enqueue(lambda n=i: slow_job(n))
    queue.wait_until_idle(timeout=5)
    elapsed = time.monotonic() - start

    assert sorted(results) == list(range(10))
    # Two real batches of 5 -- NOT ~0.3s (would mean unbounded
    # concurrency, the real "protect the server" property failing) and
    # NOT ~3s (would mean back to fully sequential).
    assert 0.5 < elapsed < 1.5, f"unexpected timing {elapsed:.2f}s -- concurrency bound may not be working"


def test_queue_depth_reflects_pending_work():
    def slow_job():
        time.sleep(0.2)

    assert queue.queue_depth() == 0
    for _ in range(3):
        queue.enqueue(slow_job)

    assert queue.queue_depth() > 0
    queue.wait_until_idle(timeout=5)
    assert queue.queue_depth() == 0


def test_a_failing_job_does_not_stop_other_jobs_from_running():
    results = []

    def failing_job():
        raise RuntimeError("simulated failure")

    def working_job(n):
        results.append(n)

    queue.enqueue(failing_job)
    queue.enqueue(lambda: working_job(1))
    queue.enqueue(lambda: working_job(2))
    queue.wait_until_idle(timeout=5)

    assert sorted(results) == [1, 2]


def test_wait_until_idle_raises_on_timeout_if_jobs_never_finish():
    def hangs_forever():
        time.sleep(10)

    queue.enqueue(hangs_forever)

    with pytest.raises(TimeoutError):
        queue.wait_until_idle(timeout=0.2)
