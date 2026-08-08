"""
Order Book -- auto-clear window resolution AND sweep application. PURE
window math plus the one shared "given a resolved window, which orders
does this actually mutate" function -- used by BOTH the HTTP-triggered
path (services/auto_clear_service.py's run_sweep, one business at a
time) and the scheduled job (jobs/auto_clear_sweep_job.py, every
eligible business per tick). Kept as ONE implementation deliberately:
two copies of "which orders are due and how to mark them" is exactly
the kind of thing that quietly drifts apart the first time either one
gets a bug fix and the other doesn't.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional

from src.domains.business.order_book.models.auto_clear_settings import (
    AUTO_CLEAR_FIXED_MINUTES,
    AutoClearDuration,
)
from src.domains.business.order_book.models.order import OrderDeletionReason, OrderStatus
from src.domains.business.order_book.repositories.order_repository import OrderRepository


def resolve_window(duration: AutoClearDuration, custom_hours: Optional[float]) -> Optional[timedelta]:
    if duration == AutoClearDuration.CUSTOM:
        if not custom_hours or custom_hours <= 0:
            return None
        return timedelta(hours=custom_hours)
    minutes = AUTO_CLEAR_FIXED_MINUTES.get(duration)
    if minutes is None:
        return None
    return timedelta(minutes=minutes)


def apply_sweep_for_scope(
    business_id: uuid.UUID,
    status: OrderStatus,
    window: timedelta,
    cause: OrderDeletionReason,
    now: datetime,
) -> int:
    """Marks every order of the given status/business that's past its
    window as deleted (moved to Trash). Does NOT commit -- the caller
    (either an HTTP request or the scheduled job, each with its own
    transaction/error-handling shape) decides when to commit. Returns
    the count mutated, for the caller's own reporting."""
    candidates = OrderRepository.list_due_for_auto_clear(business_id, status)
    cleared = 0
    for order in candidates:
        timestamp = order.completed_at if status == OrderStatus.COMPLETED else order.cancelled_at
        if timestamp is None:
            continue
        if now - timestamp >= window:
            order.is_deleted = True
            order.deleted_at = now
            order.deletion_cause = cause
            cleared += 1
    return cleared
