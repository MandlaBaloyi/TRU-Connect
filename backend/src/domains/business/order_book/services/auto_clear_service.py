"""
Order Book -- auto-clear settings and sweep.

KEPT SEPARATE FROM order_book_service.py on purpose, mirroring the
frontend's split (hooks/useAutoClearSettings.ts + algorithms/autoClearSweep.ts
vs the main order mutations). When a real scheduled job gets built
(master_scheduler/, same pattern as every other domain's scheduled
job), run_auto_clear_sweep() below becomes that job's body directly --
it already takes only a business_id and has no HTTP/request
dependencies. THAT WIRING IS NOT DONE YET: nothing in this codebase
currently calls run_auto_clear_sweep() on a timer. It is only reachable
today via the (yet to be built) HTTP route calling it directly,
matching the frontend's current mock-mode "check on screen open"
behaviour rather than a real background sweep. Flagged here rather
than silently left unwired.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from src.domains.business.order_book.models.auto_clear_settings import (
    AutoClearDuration,
    OrderBookAutoClearSettings,
)
from src.domains.business.order_book.models.order import OrderDeletionReason, OrderStatus
from src.domains.business.order_book.repositories.auto_clear_settings_repository import (
    AutoClearSettingsRepository,
)
from src.domains.business.order_book.repositories.order_repository import OrderRepository
from src.domains.business.order_book.services.errors import OrderBookValidationError
from src.domains.business.order_book.utils.auto_clear_window import resolve_window
from src.extensions import db


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AutoClearService:
    @staticmethod
    def get_settings(business_id: uuid.UUID) -> OrderBookAutoClearSettings:
        return AutoClearSettingsRepository.get_or_create_for_business(business_id)

    @staticmethod
    def set_setting(
        business_id: uuid.UUID,
        scope: str,
        duration: AutoClearDuration,
        custom_hours: Optional[float] = None,
    ) -> OrderBookAutoClearSettings:
        if duration == AutoClearDuration.CUSTOM and (not custom_hours or custom_hours <= 0):
            raise OrderBookValidationError(
                "Enter how many hours before completed/cancelled orders should move to Trash.",
                field="customHours",
            )

        settings = AutoClearSettingsRepository.get_or_create_for_business(business_id)
        if scope == "COMPLETED":
            settings.completed_duration = duration
            settings.completed_custom_hours = custom_hours if duration == AutoClearDuration.CUSTOM else None
        else:
            settings.cancelled_duration = duration
            settings.cancelled_custom_hours = custom_hours if duration == AutoClearDuration.CUSTOM else None
        db.session.commit()
        return settings

    @staticmethod
    def run_sweep(business_id: uuid.UUID) -> int:
        """Sweeps both COMPLETED and CANCELLED orders against their own
        independent settings. Returns the count moved to Trash. See
        module docstring for what "wired to a real schedule" still
        requires beyond this function existing."""
        settings = AutoClearSettingsRepository.get_or_create_for_business(business_id)
        now = _now()
        cleared = 0

        cleared += AutoClearService._sweep_scope(
            business_id, OrderStatus.COMPLETED, settings.completed_duration,
            settings.completed_custom_hours, OrderDeletionReason.AUTO_CLEAR_COMPLETED, now,
        )
        cleared += AutoClearService._sweep_scope(
            business_id, OrderStatus.CANCELLED, settings.cancelled_duration,
            settings.cancelled_custom_hours, OrderDeletionReason.AUTO_CLEAR_CANCELLED, now,
        )
        if cleared:
            db.session.commit()
        return cleared

    @staticmethod
    def _sweep_scope(
        business_id: uuid.UUID,
        status: OrderStatus,
        duration: AutoClearDuration,
        custom_hours: Optional[float],
        cause: OrderDeletionReason,
        now: datetime,
    ) -> int:
        window = resolve_window(duration, custom_hours)
        if window is None:
            return 0

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
