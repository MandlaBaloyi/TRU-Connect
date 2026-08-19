"""
Media's own scheduled jobs. Same convention as
network/connections/schedulers/connections_scheduler.py: this file
only DECLARES jobs -- the logic lives in jobs/, master_scheduler/
registry.py decides how they actually run.

Every 10 minutes, not hourly like the invitation cleanup -- a stuck
PENDING upload directly blocks a supplier from seeing whether their
photo worked; the shortest reasonable check interval matters here more
than it does for a week-scale invitation expiry.
"""
from __future__ import annotations

from src.master_scheduler.interfaces import JobSpec
from src.shared.media.jobs import stuck_media_sweep

JOB_SPECS: list[JobSpec] = [
    JobSpec(
        name="media_stuck_pending_sweep",
        func=stuck_media_sweep.run,
        interval_seconds=600,
    ),
]
