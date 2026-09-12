"""
Idempotency's scheduled job. Declares only -- the logic lives in
jobs/, and master_scheduler/registry.py decides how it runs.

HOURLY, against a 24-hour window. Precision buys nothing here: a row
removed an hour after it expired has been unreplayable for that entire
hour anyway, and the table is small enough that sweeping it more often
would only spend queries.
"""
from __future__ import annotations

from src.master_scheduler.interfaces import JobSpec
from src.shared.idempotency.jobs import expiry_sweep

JOB_SPECS: list[JobSpec] = [
    JobSpec(
        name="idempotency_expiry_sweep",
        func=expiry_sweep.run,
        interval_seconds=3600,
    ),
]
