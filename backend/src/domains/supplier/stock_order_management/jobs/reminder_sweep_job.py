"""
Job service: reminds a supplier about any order still sitting at
PENDING_SUPPLIER_APPROVAL past a real threshold -- 24 hours for the
first nudge, 3 days for the second. Handles BOTH thresholds in one
job (they're the same class of concern, nudging a supplier), unlike
auto_decline_sweep_job.py which is deliberately separate since closing
an order out is a materially different, final action.

Pure job-service contract, same as every other job in this codebase
(order_book/jobs/auto_clear_sweep_job.py,
connections/jobs/expired_invitations_cleanup_job.py): takes no
arguments, returns a JobResult, has no idea it's scheduled.

ONE JOB, EVERY SUPPLIER -- NOT ONE JOB PER SUPPLIER. Runs once per
scheduler tick and processes every eligible order in that single run,
same reasoning as order_book's own auto-clear sweep.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from src.domains.network.orders.notification_templates.stock_order_templates import (
    build_order_reminder_notification,
)
from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.extensions import db
from src.shared.notifications.notifications import publish_notification
from src.shared.scheduling.scheduling_types import JobResult

logger = logging.getLogger(__name__)

FIRST_REMINDER_AFTER = timedelta(hours=24)
SECOND_REMINDER_AFTER = timedelta(days=3)


def run() -> JobResult:
    """Sends the 24h reminder to every eligible order, then the 3-day
    reminder to every eligible order, in that order within one run.
    One order failing partway through does not stop the rest --
    matches auto_clear_sweep_job.py's own "don't let one bad row sink
    an entire sweep" reasoning."""
    now = datetime.now(timezone.utc)
    sent_count = 0

    first_due = StockOrderRepository.list_awaiting_first_reminder(now - FIRST_REMINDER_AFTER)
    for order in first_due:
        try:
            _send_reminder(order)
            order.first_reminder_sent_at = now
            db.session.commit()
            sent_count += 1
        except Exception:  # noqa: BLE001 -- one order's own failure must never sink the whole sweep
            db.session.rollback()
            logger.exception("first reminder failed for order_id=%s", order.id)

    second_due = StockOrderRepository.list_awaiting_second_reminder(now - SECOND_REMINDER_AFTER)
    for order in second_due:
        try:
            _send_reminder(order)
            order.second_reminder_sent_at = now
            db.session.commit()
            sent_count += 1
        except Exception:  # noqa: BLE001
            db.session.rollback()
            logger.exception("second reminder failed for order_id=%s", order.id)

    return JobResult(success=True, count=sent_count, detail=f"sent {sent_count} reminder(s)")


def _send_reminder(order) -> None:
    supplier = SupplierProfileRepository.get_by_id(order.supplier_profile_id)
    if not supplier:
        return
    publish_notification(
        build_order_reminder_notification(
            order,
            supplier_user_id=str(supplier.supplier_id),
            buyer_business_name=order.buyer_business_name or order.buyer_name or "A business",
        )
    )
