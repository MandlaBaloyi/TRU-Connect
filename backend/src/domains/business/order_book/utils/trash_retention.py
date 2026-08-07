"""
Order Book -- trash retention. PURE. Mirrors the frontend's
algorithms/trashRetention.ts exactly (same 7-day window, same
"clamp at 0, never negative" rule) so the backend and the client
that's currently running against mock data agree once they're
connected.
"""
from __future__ import annotations

from datetime import datetime, timezone

TRASH_RETENTION_DAYS = 7


def days_remaining_in_trash(deleted_at: datetime, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    elapsed_days = (now - deleted_at).days
    return max(0, TRASH_RETENTION_DAYS - elapsed_days)


def is_expired_from_trash(deleted_at: datetime, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    return (now - deleted_at).days >= TRASH_RETENTION_DAYS
