"""
Job service: moves completed/cancelled orders to Trash once they've
sat past whatever auto-clear window each business has configured.

ONE JOB, MANY BUSINESSES -- NOT ONE JOB PER BUSINESS. This runs once
per scheduler tick and processes every eligible business inside that
single run. At 100,000 businesses this is still one job, one query to
find who's eligible, then a loop -- not 100,000 scheduled jobs. See
AutoClearSettingsRepository.list_enabled() for the "who's eligible"
query, which already skips any business that's never turned auto-clear
on at all, so a business with it OFF costs this job nothing beyond one
row in that initial query.

This is a pure business-logic job service, not a scheduled task in its
own right: it takes no arguments, returns a JobResult, and has no idea
it's scheduled -- same contract as
domains/auth/jobs/cleanup_unverified_emails.py. It could be called from
a script, a test, or a scheduler without any difference in behavior.
Only this feature's own scheduler file
(schedulers/order_book_scheduler.py) knows this function is scheduled,
and decides how often.

TIMING IS APPROXIMATE ON PURPOSE. "5 minutes" doesn't mean the order
moves at exactly 12:05:00.000 -- it means the NEXT time this job runs
after 12:05:00, which at a 1-minute tick could be 12:05:xx or 12:06:xx.
That's a deliberate, reasonable trade-off (see this job's scheduler
entry for the interval), not a bug -- nobody needs millisecond
precision on "clean up my completed orders eventually."

REUSES apply_sweep_for_scope() FROM utils/auto_clear_window.py --
the exact same function services/auto_clear_service.py's HTTP-triggered
run_sweep() calls. One implementation of "which orders are due", used
from both the request path and this scheduled path, so a future bug
fix can't accidentally land in only one of them.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.domains.business.order_book.models.order import OrderDeletionReason, OrderStatus
from src.domains.business.order_book.repositories.auto_clear_settings_repository import (
    AutoClearSettingsRepository,
)
from src.domains.business.order_book.utils.auto_clear_window import apply_sweep_for_scope, resolve_window
from src.extensions import db
from src.shared.scheduling.scheduling_types import JobResult

logger = logging.getLogger(__name__)


def run() -> JobResult:
    """
    Sweeps every business that has auto-clear enabled for completed
    and/or cancelled orders, moving anything past its window into
    Trash. Each business's own two settings (completed, cancelled) are
    evaluated independently -- see AutoClearScope in the frontend's
    types.ts for why they're never shared.

    One business failing partway through (e.g. an unexpected data
    issue) does not stop the sweep for every other business queued
    behind it -- each business's work is its own try/except, logged and
    skipped, not a single all-or-nothing transaction across everyone.

    Must run inside an active Flask app context (db.session is
    context-bound) -- Master Scheduler's trigger guarantees this
    automatically, same as every other registered job.
    """
    now = datetime.now(timezone.utc)
    total_cleared = 0
    businesses_processed = 0
    businesses_failed = 0

    eligible_settings = AutoClearSettingsRepository.list_enabled()

    for settings in eligible_settings:
        try:
            cleared_here = 0

            completed_window = resolve_window(settings.completed_duration, settings.completed_custom_hours)
            if completed_window is not None:
                cleared_here += apply_sweep_for_scope(
                    settings.business_id, OrderStatus.COMPLETED, completed_window,
                    OrderDeletionReason.AUTO_CLEAR_COMPLETED, now,
                )

            cancelled_window = resolve_window(settings.cancelled_duration, settings.cancelled_custom_hours)
            if cancelled_window is not None:
                cleared_here += apply_sweep_for_scope(
                    settings.business_id, OrderStatus.CANCELLED, cancelled_window,
                    OrderDeletionReason.AUTO_CLEAR_CANCELLED, now,
                )

            if cleared_here:
                db.session.commit()
            total_cleared += cleared_here
            businesses_processed += 1

        except Exception:
            db.session.rollback()
            businesses_failed += 1
            logger.exception(
                "order_book_auto_clear_sweep: failed for business_id=%s, continuing with remaining businesses",
                settings.business_id,
            )

    detail = (
        f"processed {businesses_processed} business(es), "
        f"moved {total_cleared} order(s) to Trash"
        + (f", {businesses_failed} business(es) failed" if businesses_failed else "")
    )
    logger.info("order_book_auto_clear_sweep: %s", detail)
    return JobResult(success=businesses_failed == 0, count=total_cleared, detail=detail)
