"""
Job service: closes out any order still sitting at
PENDING_SUPPLIER_APPROVAL past the real, final timeout -- 7 days
unanswered. Genuinely separate from reminder_sweep_job.py, not folded
into it, since this is a materially different, final action (closing
an order out for good) rather than a nudge.

Reuses order_management_service.auto_decline_order for the actual
state change -- the SAME core logic (status, reservation release) a
manual decline uses, via that function's own shared _apply_decline
helper -- so this sweep can never drift from what a real supplier
decline does to the data.

Pure job-service contract, same as every other job in this codebase.
Takes no arguments, returns a JobResult, has no idea it's scheduled.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository
from src.domains.supplier.stock_order_management.services import order_management_service
from src.extensions import db
from src.shared.scheduling.scheduling_types import JobResult

logger = logging.getLogger(__name__)

AUTO_DECLINE_AFTER = timedelta(days=7)


def run() -> JobResult:
    """Auto-declines every order that has sat PENDING_SUPPLIER_APPROVAL
    for 7 days or more, releasing its reserved stock and notifying the
    business honestly that it timed out. One order's own failure does
    not stop the rest of the sweep."""
    now = datetime.now(timezone.utc)
    due = StockOrderRepository.list_awaiting_auto_decline(now - AUTO_DECLINE_AFTER)

    closed_count = 0
    for order in due:
        try:
            order_management_service.auto_decline_order(order)
            closed_count += 1
        except Exception:  # noqa: BLE001 -- one order's own failure must never sink the whole sweep
            db.session.rollback()
            logger.exception("auto-decline failed for order_id=%s", order.id)

    return JobResult(success=True, count=closed_count, detail=f"auto-declined {closed_count} order(s)")
