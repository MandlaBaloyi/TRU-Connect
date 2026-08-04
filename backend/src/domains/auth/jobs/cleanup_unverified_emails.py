"""
Job service: deletes User accounts whose EMAIL was never verified, once
abandoned longer than UNVERIFIED_EMAIL_CLEANUP_DAYS.

SCOPE — READ BEFORE EXTENDING THIS FILE: this concerns ONLY
User.verification_status (email/OTP verification, set during the auth
registration flow). It has NO relationship to future Business/Supplier
PROFILE verification (KYC/trust-style document checks), which will live in
its own domain (verification/ or trust/) with its own model and, if ever
needed, its own separate cleanup job. Do not repurpose this file to cover
profile verification — write a new job service instead, in the domain
that owns that concept.

This is a pure business-logic job service, not a scheduled task in its own
right: it takes no arguments, returns a JobResult, and has no idea it's
scheduled. It could be called from a script, a test, or a scheduler
without any difference in behavior. Platform
(src/domains/platform/schedulers/registry.py) is the only thing that knows
this function is scheduled, and decides how often.

This is a SWEEP for rows nobody ever came back to touch. It is distinct
from (and does not overlap with) the 24-hour resume-window logic in
auth_service, which only fires lazily when someone attempts to re-register
or log in with the same email — this job requires no such attempt; it
runs on its own schedule.

Consistent with the existing hard-delete decision for the 24h-past-window
case: the email UNIQUE constraint means soft-delete would permanently
reserve the address, so this job hard-deletes too.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from src.domains.auth.models.user import User, VerificationStatus
from src.domains.security.rules.thresholds import (
    UNVERIFIED_EMAIL_CLEANUP_BATCH_SIZE,
    UNVERIFIED_EMAIL_CLEANUP_DAYS,
)
from src.extensions import db
from src.shared.scheduling.scheduling_types import JobResult

logger = logging.getLogger(__name__)


def run() -> JobResult:
    """
    Deletes unverified-email accounts older than
    UNVERIFIED_EMAIL_CLEANUP_DAYS. Deletes in batches
    (UNVERIFIED_EMAIL_CLEANUP_BATCH_SIZE rows at a time) rather than one
    giant DELETE, so this never holds a long lock on the users table while
    live registration/login traffic is happening. Each batch is its own
    transaction — safe to interrupt between batches.

    Idempotent: running this twice back-to-back is safe. The second run's
    query simply matches nothing, because the first run already deleted
    the qualifying rows.

    Must run inside an active Flask app context (db.session is
    context-bound) — Platform's scheduler guarantees this automatically;
    see platform/schedulers/trigger.py. If calling this directly (e.g.
    from a script or shell), wrap the call in `with app.app_context():`
    yourself.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=UNVERIFIED_EMAIL_CLEANUP_DAYS)
    total_deleted = 0

    try:
        while True:
            candidate_ids = [
                row.id
                for row in (
                    db.session.query(User.id)
                    .filter(
                        User.verification_status == VerificationStatus.UNVERIFIED,
                        User.created_at < cutoff,
                    )
                    .limit(UNVERIFIED_EMAIL_CLEANUP_BATCH_SIZE)
                    .all()
                )
            ]
            if not candidate_ids:
                break

            (
                db.session.query(User)
                .filter(User.id.in_(candidate_ids))
                .delete(synchronize_session=False)
            )
            db.session.commit()
            total_deleted += len(candidate_ids)

            if len(candidate_ids) < UNVERIFIED_EMAIL_CLEANUP_BATCH_SIZE:
                break  # last (partial) batch — no more candidates remain

        detail = (
            f"deleted {total_deleted} unverified-email account(s) "
            f"older than {UNVERIFIED_EMAIL_CLEANUP_DAYS} day(s)"
        )
        logger.info("cleanup_unverified_emails: %s", detail)
        return JobResult(success=True, count=total_deleted, detail=detail)

    except Exception:
        db.session.rollback()
        raise
