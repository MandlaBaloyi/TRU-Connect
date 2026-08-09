"""Business Profile data access. get_or_create means every business
implicitly has a profile row (defaulting to an empty one with just a
placeholder name) without needing a migration-time backfill or a
nullable-profile check scattered through the service layer -- same
reasoning as Order Book's AutoClearSettingsRepository."""
from __future__ import annotations

import uuid
from typing import Optional

from src.domains.business.business_profile.models.business_profile import BusinessProfile
from src.extensions import db


class BusinessProfileRepository:
    @staticmethod
    def get_for_business(business_id: uuid.UUID) -> Optional[BusinessProfile]:
        return BusinessProfile.query.filter_by(business_id=business_id).first()

    @staticmethod
    def get_or_create_for_business(business_id: uuid.UUID, default_name: str = "") -> BusinessProfile:
        profile = BusinessProfileRepository.get_for_business(business_id)
        if profile is None:
            profile = BusinessProfile(
                id=uuid.uuid4(),
                business_id=business_id,
                business_name=default_name,
            )
            db.session.add(profile)
            db.session.flush()
        return profile
