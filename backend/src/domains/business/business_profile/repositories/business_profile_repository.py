"""Business Profile data access. get_or_create means every business
implicitly has a profile row (defaulting to an empty one with just a
placeholder name) without needing a migration-time backfill or a
nullable-profile check scattered through the service layer -- same
reasoning as Order Book's AutoClearSettingsRepository.

search_by_name_prefix -- added for Find Business (network/connections'
own supplier-side mirror of Find Supplier). PREFIX-ONLY, never a
substring scan (file.txt §4 privacy rule, applied identically in both
directions).

search_by_phone/search_by_email were REMOVED -- previously present
here (mirroring SupplierProfileRepository's own, since deleted), used
only by connections/services _common._dispatch_search. Search is
name/business-name only now; see that function's own docstring for the
full reasoning. normalized_phone/normalized_email columns stay on the
model -- they're unrelated to search (kept in sync by
business_profile_service.py, see that file)."""
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
    def get_or_create_for_business(
        business_id: uuid.UUID, default_name: str | None = None
    ) -> BusinessProfile:
        """The row, creating it if this business has never had one.

        THE NAME FALLS BACK TO users.business_name WHEN THE CALLER GIVES
        NONE, and that default is the fix for a real hole rather than a
        nicety. Almost every caller here passes nothing -- get_profile
        and all six PATCH routes do -- and the old default was the empty
        string. That is invisible in the normal flow, because
        otp_service seeds the profile with the real name at verification
        and every route on this domain is @fully_authenticated, so the
        row already exists by the time a PATCH runs.

        But _seed_business_profile is deliberately wrapped in a
        try/except that logs and continues -- a failed profile seed must
        not fail somebody's email verification. When it does fail, the
        first PATCH creates the row instead, and under the old default
        that shop was nameless permanently: invisible in Find Business,
        blank on every connection request, and with nothing anywhere to
        say why.

        Reading the name off the user costs one query on the path that
        was already creating a row, and makes the fallback correct
        instead of empty.
        """
        profile = BusinessProfileRepository.get_for_business(business_id)
        if profile is None:
            if default_name is None:
                from src.domains.auth.models.user import User

                user = db.session.get(User, business_id)
                default_name = (
                    (user.business_name if user else None)
                    or " ".join(
                        filter(None, [getattr(user, "first_name", None), getattr(user, "last_name", None)])
                    ).strip()
                    or ""
                )

            profile = BusinessProfile(
                id=uuid.uuid4(),
                business_id=business_id,
                business_name=default_name,
            )
            db.session.add(profile)
            db.session.flush()
        return profile

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

    @staticmethod
    def declared_categories_by_business() -> dict:
        """{business_id: [category, ...]} for every shop that answered.

        THE DECLARED HALF OF THE GAP REPORT. Shops that declared
        nothing are ABSENT rather than present-and-empty: they have not
        told us they need anything, so they cannot be counted as
        unserved, and an empty list would quietly become a zero in an
        average somewhere.

        TWO COLUMNS, NOT WHOLE ROWS. This is read across the entire
        platform, and hydrating full BusinessProfile objects to look at
        one array each is the kind of waste that only shows up at the
        scale where it matters.
        """
        rows = (
            db.session.query(BusinessProfile.business_id, BusinessProfile.buys_categories)
            .filter(BusinessProfile.buys_categories.isnot(None))
            .filter(BusinessProfile.is_deleted.is_(False))
            .all()
        )
        return {
            str(business_id): list(categories)
            for business_id, categories in rows
            if categories
        }

