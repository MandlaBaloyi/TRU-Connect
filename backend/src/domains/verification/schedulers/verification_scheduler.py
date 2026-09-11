"""
Verification's own scheduled jobs. Same convention as
stock_order_management/schedulers: this file only DECLARES jobs (name,
function, interval) -- the logic lives in jobs/, and
master_scheduler/registry.py decides how they actually run.

INTERVAL: six hours. The shortest rung on the ladder is a full DAY, so
checking more often buys nothing -- a supplier reminded within six
hours of crossing the one-day mark is far more precise than the
decision it is nudging. Same "approximate timing on purpose" reasoning
as the stock-order reminder sweep, one notch slower because the
thresholds here are days rather than hours.
"""
from __future__ import annotations

from src.domains.verification.jobs import verification_reminder_sweep
from src.master_scheduler.interfaces import JobSpec

JOB_SPECS: list[JobSpec] = [
    JobSpec(
        name="verification_reminder_sweep",
        func=verification_reminder_sweep.run,
        interval_seconds=6 * 3600,
    ),
]
