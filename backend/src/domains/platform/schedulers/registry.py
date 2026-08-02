"""
The explicit list of what's scheduled and how often.

Platform decides WHEN; the imported functions decide WHAT. Each entry
below is a business domain's job service (e.g.
auth.jobs.cleanup_unverified_emails.run) — a plain function that returns a
JobResult and knows nothing about scheduling.

This file is the one and only place that imports job services FROM
business domains INTO platform. The dependency runs Platform -> Auth,
never Auth -> Platform: Auth's job service files never import anything
under domains/platform.

To add a new scheduled job:
    1. Write the job service in its owning domain (a run() function,
       takes no arguments, returns a JobResult).
    2. Add one line to JOB_SPECS below.
Nothing else needs to change.
"""

from __future__ import annotations

from typing import Callable, NamedTuple, Optional

from src.domains.auth.jobs.cleanup_unverified_emails import run as cleanup_unverified_emails
from src.domains.platform.schedulers import runner
from src.domains.platform.schedulers.interfaces import SchedulerEngine
from src.shared.scheduling_types import JobResult


class JobSpec(NamedTuple):
    name: str
    func: Callable[[], JobResult]
    interval_seconds: float


# How often each job runs — a PLATFORM ("when") decision, distinct from
# any business threshold the job itself applies (e.g. "how many days old
# counts as abandoned" lives in the owning domain's own rules, not here —
# see src/domains/security/rules/thresholds.py for the auth example).
JOB_SPECS: list[JobSpec] = [
    JobSpec(
        name="cleanup_unverified_emails",
        func=cleanup_unverified_emails,
        interval_seconds=24 * 60 * 60,  # once a day
    ),
    # Future jobs slot in here as a one-line addition each, e.g.:
    # JobSpec("cleanup_expired_password_reset_tokens", cleanup_expired_password_reset_tokens.run, 24 * 60 * 60),
    # JobSpec("cleanup_expired_otps", cleanup_expired_otps.run, 6 * 60 * 60),
    # JobSpec("cleanup_expired_refresh_tokens", cleanup_expired_refresh_tokens.run, 24 * 60 * 60),
]


def register_all(engine: SchedulerEngine, context_factory: Optional[Callable] = None) -> None:
    """
    Wrap every JobSpec's function with runner.make_safe() and hand it to
    the engine. `context_factory`, if given, is threaded through to every
    job (e.g. Flask app-context wrapping) — see trigger.py, the only
    caller that knows about Flask.
    """
    for spec in JOB_SPECS:
        safe_func = runner.make_safe(spec.name, spec.func, context_factory=context_factory)
        engine.add_job(spec.name, safe_func, spec.interval_seconds)
