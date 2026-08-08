"""
Order Book's own scheduled jobs. Same convention as
domains/auth/schedulers/auth_scheduler.py: this file only DECLARES
jobs (name, function, interval) -- the actual logic lives in jobs/,
and master_scheduler/registry.py decides how they actually run.

This is the FIRST business-domain scheduler in this codebase -- Loan
Book has no scheduled job today (see order_book_service.py's sibling
discussion on why: its own "aging/overdue" concept is computed live on
every read, not something a background job needs to flip). If Loan
Book or another business feature ever needs one, it gets its own
sibling file here (e.g. domains/business/loan_book/schedulers/
loan_book_scheduler.py), following this exact same shape.

INTERVAL: every 60 seconds. The shortest configurable auto-clear
duration is 5 minutes, so a 1-minute tick means an order becomes
eligible and is swept within roughly a minute of crossing its window --
not instant, and deliberately not meant to be (see
jobs/auto_clear_sweep_job.py's docstring on approximate timing).
"""
from __future__ import annotations

from src.domains.business.order_book.jobs import auto_clear_sweep_job
from src.master_scheduler.interfaces import JobSpec

JOB_SPECS: list[JobSpec] = [
    JobSpec(
        name="order_book_auto_clear_sweep",
        func=auto_clear_sweep_job.run,
        interval_seconds=60,
    ),
]
