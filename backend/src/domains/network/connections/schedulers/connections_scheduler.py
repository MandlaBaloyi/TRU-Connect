"""
Network Connections' own scheduled jobs. Same convention as
domains/business/order_book/schedulers/order_book_scheduler.py: this
file only DECLARES jobs (name, function, interval) -- the actual logic
lives in jobs/, and master_scheduler/registry.py decides how they
actually run.

INTERVAL: every hour, not every minute like Order Book's own sweep.
The shortest meaningful window here is the invitation ticket's own
expiry (days, not minutes -- DEFAULT_SUPPLIER_INVITATION_EXPIRY_HOURS
is 168), so there's no value in checking more often than that; an
hourly tick means an expired, never-used ticket gets swept within an
hour of expiring, which is more than precise enough for a cleanup job,
not a user-facing deadline.
"""
from __future__ import annotations

from src.domains.network.connections.jobs import expired_invitations_cleanup_job
from src.master_scheduler.interfaces import JobSpec

JOB_SPECS: list[JobSpec] = [
    JobSpec(
        name="connections_expired_invitations_cleanup",
        func=expired_invitations_cleanup_job.run,
        interval_seconds=3600,
    ),
]
