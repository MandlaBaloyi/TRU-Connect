"""
Auth Scheduler -- the Auth domain's own child scheduler, per the Master
Scheduler architecture:

    Master Scheduler
            |
     +------+----------------+
     |                       |
     v                       v
  Auth Scheduler   ...other domains' own scheduler files

This file is the ONLY place that decides Auth wants
cleanup_unverified_emails scheduled, and how often. The job's actual
logic stays exactly where it already lived
(domains/auth/jobs/cleanup_unverified_emails.py) and knows nothing about
being scheduled -- this file is what schedules it.

Add Auth's next scheduled job here as one more line, e.g. an OTP or
expired-token cleanup once those exist -- no other file needs to change.
"""

from __future__ import annotations

from src.domains.auth.jobs.cleanup_unverified_emails import run as cleanup_unverified_emails
from src.master_scheduler.interfaces import JobSpec

JOB_SPECS: list[JobSpec] = [
    JobSpec(
        name="cleanup_unverified_emails",
        func=cleanup_unverified_emails,
        interval_seconds=24 * 60 * 60,  # once a day
    ),
    # Future Auth jobs slot in here, e.g.:
    # JobSpec("cleanup_expired_otps", cleanup_expired_otps.run, 6 * 60 * 60),
    # JobSpec("cleanup_expired_password_reset_tokens", cleanup_expired_password_reset_tokens.run, 24 * 60 * 60),
]
