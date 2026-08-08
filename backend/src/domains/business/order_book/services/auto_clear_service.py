"""
Order Book -- auto-clear settings and sweep.

KEPT SEPARATE FROM order_book_service.py on purpose, mirroring the
frontend's split (hooks/useAutoClearSettings.ts + algorithms/autoClearSweep.ts
vs the main order mutations).

run_sweep() below is the HTTP-triggered path (still used by the
frontend's manual/polling trigger). The REAL scheduled path is
jobs/auto_clear_sweep_job.py, registered in
schedulers/order_book_scheduler.py and wired into master_scheduler --
both this and the job call the same shared
utils/auto_clear_window.apply_sweep_for_scope() for the actual sweep
logic, so there is exactly one implementation of "which orders are
due", not two that could drift apart.
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
from src.domains.business.order_book.services.errors import OrderBookValidationError
from src.domains.business.order_book.utils.auto_clear_window import apply_sweep_for_scope, resolve_window
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
        independent settings, for ONE business, triggered by an HTTP
        request. Returns the count moved to Trash."""
        settings = AutoClearSettingsRepository.get_or_create_for_business(business_id)
        now = _now()
        cleared = 0

        completed_window = resolve_window(settings.completed_duration, settings.completed_custom_hours)
        if completed_window is not None:
            cleared += apply_sweep_for_scope(
                business_id, OrderStatus.COMPLETED, completed_window,
                OrderDeletionReason.AUTO_CLEAR_COMPLETED, now,
            )

        cancelled_window = resolve_window(settings.cancelled_duration, settings.cancelled_custom_hours)
        if cancelled_window is not None:
            cleared += apply_sweep_for_scope(
                business_id, OrderStatus.CANCELLED, cancelled_window,
                OrderDeletionReason.AUTO_CLEAR_CANCELLED, now,
            )

        if cleared:
            db.session.commit()
        return cleared
