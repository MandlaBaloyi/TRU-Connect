"""
Job service: nudges suppliers who are still invisible to buyers.

THREE RUNGS, THEN SILENCE. Day 1, day 3, day 7 after the curtain
closed -- and then nothing, ever. The thing being waited on is OUR
decision, not theirs; a fourth email would be nagging somebody about
work they cannot do anything about.

Pure job-service contract, same as every other job in this codebase
(stock_order_management/jobs/reminder_sweep_job.py,
order_book/jobs/auto_clear_sweep_job.py): takes no arguments, returns
a JobResult, has no idea it is scheduled.

ONE JOB, EVERY SUPPLIER -- NOT ONE JOB PER SUPPLIER. One pass per tick
handles every eligible profile, and one failing row does not sink the
sweep.

THE CLOCK IS verification_reminder_sent_at, FALLING BACK TO created_at.
That fallback is what stops every existing unverified supplier being
sent all three emails in the first sweep after deploy -- they get rung
one, then wait the real interval for rung two like everybody else.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from src.core.base_model import utcnow
from src.domains.supplier.supplier_profile.models.supplier_profile import (
    SupplierProfile,
    SupplierVerificationStatus,
)
from src.domains.verification.notification_templates import verification_emails
from src.extensions import db
from src.shared.scheduling.scheduling_types import JobResult

logger = logging.getLogger(__name__)

#: How long after the PREVIOUS tick each rung becomes due. Cumulative
#: from the moment the curtain closed, these land on roughly day 1,
#: day 3 and day 7.
RUNG_DELAYS = (timedelta(days=1), timedelta(days=2), timedelta(days=4))


def run() -> JobResult:
    now = utcnow()
    sent = 0
    failed = 0

    candidates = (
        SupplierProfile.query.filter(
            SupplierProfile.is_deleted.is_(False),
            SupplierProfile.verification_status == SupplierVerificationStatus.UNVERIFIED,
            SupplierProfile.verification_reminder_stage < verification_emails.LADDER_LENGTH,
        )
        .order_by(SupplierProfile.created_at.asc())
        .all()
    )

    for profile in candidates:
        stage = profile.verification_reminder_stage or 0
        since = profile.verification_reminder_sent_at or profile.created_at
        if since is None or now - since < RUNG_DELAYS[stage]:
            continue

        try:
            _send(profile, stage)
            # STAMPED EVEN THOUGH EmailService NEVER RAISES, and that is
            # deliberate: the alternative is that an unreachable mail
            # server leaves the stage unchanged and the next tick tries
            # the same supplier again, an hour later, forever. A missed
            # reminder is a gap; an hourly retry loop against somebody's
            # inbox is a different kind of problem.
            profile.verification_reminder_stage = stage + 1
            profile.verification_reminder_sent_at = now
            db.session.commit()
            sent += 1
        except Exception:  # noqa: BLE001
            db.session.rollback()
            failed += 1
            logger.exception(
                "verification reminder failed for supplier_profile=%s stage=%s", profile.id, stage
            )

    # count = what was actually DONE, detail = the sentence a human
    # reads. `considered` is in the detail rather than the count
    # because a sweep that looked at 200 suppliers and emailed none is
    # a quiet success, not 200 units of work.
    return JobResult(
        success=True,
        count=sent,
        detail=f"{sent} sent, {failed} failed, {len(candidates)} considered",
    )


def _send(profile, stage: int) -> None:
    from src.domains.auth.repositories.user_repository import UserRepository
    from src.shared.email.email import EmailService

    user = UserRepository.get_by_id(profile.supplier_id)
    if user is None or not user.email:
        # NOT AN ERROR, and it must not stamp the stage either -- a
        # profile whose user row is missing is a data problem to notice,
        # not a reminder to mark as delivered.
        raise ValueError(f"no reachable user for supplier_profile={profile.id}")

    template_name, subject, context = verification_emails.reminder(user, profile, stage)
    EmailService.send_template(
        to=user.email, template_name=template_name, subject=subject, context=context
    )
