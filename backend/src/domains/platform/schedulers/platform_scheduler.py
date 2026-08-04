"""
Platform Scheduler -- the Platform domain's own child scheduler.

Empty today, honestly: Audit Cleanup, Backups, and Monitoring (per the
Master Scheduler architecture) aren't built yet. An empty JOB_SPECS list
here is the accurate statement of that -- not a placeholder pretending
jobs exist, just "this domain has declared nothing yet, correctly,
because there's nothing real to declare."
"""

from __future__ import annotations

from src.master_scheduler.interfaces import JobSpec

JOB_SPECS: list[JobSpec] = [
    # Future Platform jobs slot in here, e.g.:
    # JobSpec("audit_cleanup", audit_cleanup.run, 24 * 60 * 60),
    # JobSpec("backup_database", backup_database.run, 24 * 60 * 60),
]
