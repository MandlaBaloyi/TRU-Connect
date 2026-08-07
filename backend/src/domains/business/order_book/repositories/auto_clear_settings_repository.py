"""Auto-clear settings data access. One row per business -- get_or_create
means every business implicitly has settings (defaulting to OFF/OFF)
without needing a migration-time backfill or a nullable-settings check
scattered through the service layer."""
from __future__ import annotations

import uuid
from typing import Optional

from src.domains.business.order_book.models.auto_clear_settings import OrderBookAutoClearSettings
from src.extensions import db


class AutoClearSettingsRepository:
    @staticmethod
    def get_for_business(business_id: uuid.UUID) -> Optional[OrderBookAutoClearSettings]:
        return OrderBookAutoClearSettings.query.filter_by(business_id=business_id).first()

    @staticmethod
    def get_or_create_for_business(business_id: uuid.UUID) -> OrderBookAutoClearSettings:
        settings = AutoClearSettingsRepository.get_for_business(business_id)
        if settings is None:
            settings = OrderBookAutoClearSettings(id=uuid.uuid4(), business_id=business_id)
            db.session.add(settings)
            db.session.flush()
        return settings
