"""Business Profile data access. get_or_create means every business
implicitly has a profile row (defaulting to an empty one with just a
placeholder name) without needing a migration-time backfill or a
nullable-profile check scattered through the service layer -- same
reasoning as Order Book's AutoClearSettingsRepository.

search_by_phone/search_by_email/search_by_name_prefix -- added for
Find Business (network/connections' own supplier-side mirror of
Find Supplier). Same conventions as SupplierProfileRepository's own
search methods: phone/email take an ALREADY-NORMALIZED value, name
search is PREFIX-ONLY, never a substring scan (file.txt §4 privacy
rule, applied identically in both directions)."""
from __future__ import annotations

import uuid
from typing import List, Optional

from src.domains.business.business_profile.models.business_profile import BusinessProfile
from src.extensions import db


class BusinessProfileRepository:
    @staticmethod
    def get_for_business(business_id: uuid.UUID) -> Optional[BusinessProfile]:
        return BusinessProfile.query.filter_by(business_id=business_id).first()

    @staticmethod
    def get_by_id(business_profile_id: uuid.UUID) -> Optional[BusinessProfile]:
        return BusinessProfile.query.filter_by(id=business_profile_id).first()

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

    @staticmethod
    def search_by_phone(normalized_phone: str) -> Optional[BusinessProfile]:
        return BusinessProfile.query.filter_by(normalized_phone=normalized_phone).first()

    @staticmethod
    def search_by_email(normalized_email: str) -> Optional[BusinessProfile]:
        return BusinessProfile.query.filter_by(normalized_email=normalized_email).first()

    @staticmethod
    def search_by_name_prefix(name_query: str, limit: int = 20) -> List[BusinessProfile]:
        """Case-insensitive PREFIX match only -- same escaping fix as
        SupplierProfileRepository's own search_by_name_prefix, see
        that method's own docstring for the full reasoning."""
        from src.shared.validation.identifiers import escape_like_pattern

        pattern = f"{escape_like_pattern(name_query)}%"
        return (
            BusinessProfile.query.filter(BusinessProfile.business_name.ilike(pattern, escape="\\"))
            .order_by(BusinessProfile.business_name.asc())
            .limit(limit)
            .all()
        )
