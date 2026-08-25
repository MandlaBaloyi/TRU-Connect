"""
Generic background task queue.
 "Shared Notification Infrastructure"  "ASYNC
PROCESSING" -- "Email sending must never block HTTP requests."

DESIGN
------
A bounded pool of in-process daemon threads (concurrent.futures.
ThreadPoolExecutor), not a single worker thread. This is intentionally
NOT email-specific, and NOT bulk-import-specific -- it exists so
EmailService, AuditService, and BulkImport can all enqueue "do this in
the background" work without any of them needing their own threading
logic.

REAL BUG FOUND DURING REVIEW, NOW FIXED: this used to be exactly ONE
worker thread pulling jobs off a queue.Queue, one at a time. That meant
two suppliers submitting bulk imports even a second apart would have
the SECOND one wait, fully queued, until the FIRST one's entire job
finished -- not true concurrency at all, a genuine scalability ceiling.
A bounded pool of BACKGROUND_WORKER_POOL_SIZE threads (default 5) lets
that many jobs genuinely run at once.

THIS BOUND IS ALSO THE REAL "PROTECT THE SERVER" MECHANISM, not just a
throughput fix -- even if many different accounts submitted heavy jobs
in the same second, at most BACKGROUND_WORKER_POOL_SIZE of them are
ever actively processing simultaneously; everything past that queues
safely rather than each grabbing unbounded resources. This is what
actually protects the process itself, independent of which specific
account is doing the asking -- see bulk_import's own abuse_tracking.py
for the complementary, per-account layer sitting in front of this.

THIS IS EXPLICITLY STILL A PLACEHOLDER FOR A REAL MESSAGE BROKER --
swapping it for Celery/RQ/Dramatiq/SQS/Pub-Sub later (needed once TRU
Connect genuinely runs across MULTIPLE servers, not just multiple
threads on one) means changing only this file's own internals. No
caller of `enqueue()` needs to change, because none of them know or
care HOW the job actually runs -- true before this change, still true
after it.
"""
from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Callable, Optional

logger = logging.getLogger("tru_connect.queue")

# How many jobs can genuinely run AT THE SAME TIME. Tune via env var,
# no code change needed -- same "real constant, overridable per
# environment" pattern used throughout this build (e.g.
# CLOUDINARY_MODERATION_ENABLED).
MAX_WORKERS = int(os.environ.get("BACKGROUND_WORKER_POOL_SIZE", "5"))

_executor: Optional[ThreadPoolExecutor] = None
_executor_lock = Lock()

# ThreadPoolExecutor has no built-in "how many tasks are currently
# queued or running" introspection -- tracked explicitly instead of
# reaching into its private internals.
_pending_count = 0
_pending_lock = Lock()


def _ensure_executor_started() -> ThreadPoolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="tru-connect-worker")
    return _executor


def _run_and_track(job: Callable[[], None]) -> None:
    try:
        job()
    except Exception:  # noqa: BLE001 - a failing job must never kill the worker
        logger.exception("Background job raised an unhandled exception")
    finally:
        global _pending_count
        with _pending_lock:
            _pending_count -= 1


def enqueue(job: Callable[[], None]) -> None:
    """Schedules `job` (a zero-argument callable) to run on the
    background thread pool, and returns immediately. Starts the pool
    lazily on first use. Same public signature as before this change --
    every existing caller (email, audit, bulk import) needs zero
    changes."""
    global _pending_count
    executor = _ensure_executor_started()
    with _pending_lock:
        _pending_count += 1
    executor.submit(_run_and_track, job)


def queue_depth() -> int:
    """Approximate number of jobs currently queued or actively
    running -- used for monitoring (master prompt: "Track... Queue
    depth")."""
    with _pending_lock:
        return _pending_count


def wait_until_idle(timeout: Optional[float] = None) -> None:
    """Blocks until every currently-enqueued job has finished. Exists
    for tests -- production code should never need to wait on the
    queue. Polling-based (ThreadPoolExecutor has no native "wait for
    everything submitted so far" primitive short of shutting the whole
    pool down, which would break future enqueue() calls)."""
    start = time.monotonic()
    while queue_depth() > 0:
        if timeout is not None and (time.monotonic() - start) > timeout:
            raise TimeoutError("Timed out waiting for background jobs to finish")
        time.sleep(0.01)
