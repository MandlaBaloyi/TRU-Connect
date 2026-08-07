"""
Order Book -- auto-clear window resolution. PURE. Mirrors the
frontend's algorithms/autoClearSweep.ts resolveWindowMs exactly:
CUSTOM with a missing/invalid hour count resolves to "disabled" rather
than guessing, for the same reason stated there -- an unset custom
value must never silently clear orders immediately or never.

NOT YET WIRED TO A REAL SCHEDULED JOB -- see
services/auto_clear_service.py's docstring. This module only answers
"how long is the window", not "when does the sweep run".
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from src.domains.business.order_book.models.auto_clear_settings import (
    AUTO_CLEAR_FIXED_MINUTES,
    AutoClearDuration,
)


def resolve_window(duration: AutoClearDuration, custom_hours: Optional[float]) -> Optional[timedelta]:
    if duration == AutoClearDuration.CUSTOM:
        if not custom_hours or custom_hours <= 0:
            return None
        return timedelta(hours=custom_hours)
    minutes = AUTO_CLEAR_FIXED_MINUTES.get(duration)
    if minutes is None:
        return None
    return timedelta(minutes=minutes)
