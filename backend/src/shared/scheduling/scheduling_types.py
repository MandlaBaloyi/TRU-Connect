"""
Shared data contracts for the scheduling system.

Deliberately neutral ground: both a business domain's job service (e.g.
auth/jobs/cleanup_unverified_emails.py) and Platform's execution machinery
(domains/platform/schedulers/) import these types. Neither Auth nor
Platform "owns" this file — it lives in shared/ specifically so importing
it never creates a Business->Platform or Platform->Business dependency in
either direction. Security's monitoring layer also imports
JobExecutionOutcome from here for the same reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class JobResult:
    """
    What a domain job-service's run() function returns. Every job service
    (e.g. auth.jobs.cleanup_unverified_emails.run) returns one of these —
    never a bare bool, never None — so the runner, and eventually an admin
    panel, has something meaningful to show beyond pass/fail.
    """
    success: bool
    count: int = 0
    detail: Optional[str] = None


@dataclass(frozen=True)
class JobExecutionOutcome:
    """
    Published by platform.schedulers.runner after every execution attempt,
    whether the job succeeded, failed, or raised. This is the shared
    contract Security's monitoring layer listens for — Security never
    touches the engine or the registry directly, it only ever consumes
    these outcomes (see security/schedulers/monitor.py).
    """
    job_name: str
    started_at: datetime
    duration_ms: float
    success: bool
    result: Optional[JobResult] = None
    error: Optional[str] = None
