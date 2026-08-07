"""
OrderBookAutoClearSettings -- how long completed/cancelled orders sit
in the active queue before automatically moving to Trash. One row per
business. Completed and cancelled orders clear independently (their own
duration each) -- matches the frontend's AutoClearScope split: a shop
owner may want completed orders gone fast but keep cancelled ones
around longer for reference, or vice versa.

NOT YET WIRED TO A REAL SCHEDULED JOB. See services/auto_clear_service.py's
docstring for the sweep logic and what plugging this into
master_scheduler/ requires -- deliberately flagged rather than silently
half-built, matching this project's "no code path that guesses at an
unbuilt system" rule.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class AutoClearDuration(str, enum.Enum):
    OFF = "off"
    FIVE_MIN = "5_min"
    FIFTEEN_MIN = "15_min"
    CUSTOM = "custom"


# Fixed presets only, in minutes -- CUSTOM's window comes from
# custom_hours instead. Mirrors the frontend's AUTO_CLEAR_FIXED_DURATION_MS.
AUTO_CLEAR_FIXED_MINUTES = {
    AutoClearDuration.OFF: None,
    AutoClearDuration.FIVE_MIN: 5,
    AutoClearDuration.FIFTEEN_MIN: 15,
}


class OrderBookAutoClearSettings(BaseModel):
    __tablename__ = "order_book_auto_clear_settings"
    __table_args__ = (
        db.UniqueConstraint("business_id", name="uq_order_book_auto_clear_settings_business_id"),
        {"schema": "business"},
    )

    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)

    _duration_type = db.Enum(
        AutoClearDuration, name="order_book_auto_clear_duration",
        values_callable=lambda e: [m.value for m in e],
    )

    completed_duration = db.Column(_duration_type, nullable=False, default=AutoClearDuration.OFF)
    completed_custom_hours = db.Column(db.Float(), nullable=True)

    cancelled_duration = db.Column(_duration_type, nullable=False, default=AutoClearDuration.OFF)
    cancelled_custom_hours = db.Column(db.Float(), nullable=True)
