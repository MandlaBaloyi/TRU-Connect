"""
Generic background task queue.
Ref: "Shared Notification Infrastructure" master prompt, "ASYNC
PROCESSING" -- "Email sending must never block HTTP requests."

DESIGN
------
A single in-process daemon thread pulling zero-argument callables off a
queue.Queue and running them. This is intentionally NOT email-specific --
it exists so EmailService (and, later, SMS/push/webhook services) can
enqueue "do this in the background" work without any of them needing
their own threading logic.

This is explicitly a placeholder for a real message broker. Swapping it
for Celery/RQ/Dramatiq/SQS/Pub-Sub later means changing only
`enqueue()`'s implementation here -- no caller of `enqueue()` needs to
change, because none of them know or care HOW the job actually runs.
"""
from __future__ import annotations

import logging
import queue
import threading
from typing import Callable

logger = logging.getLogger("tru_connect.queue")

_job_queue: "queue.Queue[Callable[[], None]]" = queue.Queue()
_worker_thread: threading.Thread | None = None
_worker_lock = threading.Lock()


def _worker_loop() -> None:
    while True:
        job = _job_queue.get()
        try:
            job()
        except Exception:  # noqa: BLE001 - a failing job must never kill the worker
            logger.exception("Background job raised an unhandled exception")
        finally:
            _job_queue.task_done()


def _ensure_worker_started() -> None:
    global _worker_thread
    with _worker_lock:
        if _worker_thread is None or not _worker_thread.is_alive():
            _worker_thread = threading.Thread(target=_worker_loop, name="tru-connect-worker", daemon=True)
            _worker_thread.start()


def enqueue(job: Callable[[], None]) -> None:
    """Schedules `job` (a zero-argument callable) to run on the
    background worker thread, and returns immediately. Starts the worker
    thread lazily on first use."""
    _ensure_worker_started()
    _job_queue.put(job)


def queue_depth() -> int:
    """Approximate number of jobs waiting to run -- used by
    src/shared/metrics.py for monitoring (master prompt: "Track... Queue
    depth")."""
    return _job_queue.qsize()


def wait_until_idle(timeout: float | None = None) -> None:
    """Blocks until every currently-queued job has finished. Exists for
    tests -- production code should never need to wait on the queue."""
    _job_queue.join()
