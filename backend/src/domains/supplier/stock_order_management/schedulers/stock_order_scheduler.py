"""
Stock Order Management's own scheduled jobs. Same convention as
domains/network/connections/schedulers/connections_scheduler.py: this
file only DECLARES jobs (name, function, interval) -- the actual logic
lives in jobs/, and master_scheduler/registry.py decides how they
actually run.

INTERVAL: every hour for both -- the shortest meaningful window here
is the 24h first-reminder threshold itself; checking far more often
than that buys nothing (an order genuinely reminded within an hour of
crossing 24h is more than precise enough), same "approximate timing on
purpose" reasoning as order_book's own auto-clear sweep.
"""
from __future__ import annotations

from src.domains.supplier.stock_order_management.jobs import auto_decline_sweep_job, reminder_sweep_job
from src.master_scheduler.interfaces import JobSpec

JOB_SPECS: list[JobSpec] = [
    JobSpec(
        name="stock_order_reminder_sweep",
        func=reminder_sweep_job.run,
        interval_seconds=3600,
    ),
    JobSpec(
        name="stock_order_auto_decline_sweep",
        func=auto_decline_sweep_job.run,
        interval_seconds=3600,
    ),
]
