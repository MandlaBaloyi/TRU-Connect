"""
SupplierProfile repository -- ONLY talks to SQLAlchemy, no business
rules, matching every other repository in this codebase (see
user_repository.py's own docstring for the same rule).

search_by_name_prefix is deliberately a PREFIX match, never a
substring/contains scan -- file.txt §4: "should NOT expose everybody".
A prefix index scan is also the only one that can actually use
ix_supplier_profiles_business_name efficiently at scale; a
leading-wildcard LIKE '%term%' can't use a plain btree index at all,
so this restriction is a genuine production-grade concern (FILE2.txt's
own framing), not just a privacy one.

search_by_phone/search_by_email were REMOVED (previously present here,
used only by connections' _common._dispatch_search) -- search
is name/business-name only now; see that function's own docstring for
the full reasoning (exact-match phone/email search is an enumeration
vector). normalized_phone/normalized_email columns themselves stay on
the model -- they're still populated at verification and still used
for the UNRELATED masked-contact-detail display on an already-existing
connection request (get_supplier_request_detail), which is a different
concern from search.

get_or_create_for_supplier MIRRORS BusinessProfileRepository's own
get_or_create_for_business exactly (see that file's docstring: "every
business implicitly has a profile row... without needing a
migration-time backfill or a nullable-profile check scattered through
the service layer"). Called from OTPService.verify_otp on a supplier's
FIRST successful email verification -- deliberately NOT at raw
registration: an unverified account can still be hard-deleted by
UserRepository.hard_delete if it never completes verification within
UNVERIFIED_ACCOUNT_EXPIRY_HOURS (auth_service.py's own
_is_unverified_expired), and supplier_profiles.supplier_id has a plain
FK to auth.users.id with no cascade -- seeding before verification
would risk exactly that hard-delete failing on an orphaned reference,
or worse, succeeding and leaving one behind.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
from src.extensions import db


class SupplierProfileRepository:
    @staticmethod
    def get_by_id(supplier_profile_id: str | uuid.UUID) -> Optional[SupplierProfile]:
        return SupplierProfile.query.filter_by(id=supplier_profile_id, is_deleted=False).first()

    @staticmethod
    def get_by_supplier_id(supplier_id: str | uuid.UUID) -> Optional[SupplierProfile]:
        return SupplierProfile.query.filter_by(supplier_id=supplier_id, is_deleted=False).first()

    @staticmethod
    def get_or_create_for_supplier(supplier_id: str | uuid.UUID, default_name: str = "") -> SupplierProfile:
        profile = SupplierProfileRepository.get_by_supplier_id(supplier_id)
        if profile is None:
            from src.domains.supplier.supplier_profile.algorithms.supplier_code_generator import (
                generate_unique_supplier_code,
            )

            profile = SupplierProfile(
                id=uuid.uuid4(),
                supplier_id=supplier_id,
                business_name=default_name,
                # A real, permanent identity assigned the moment a
                # supplier profile is genuinely created, not something
                # bolted on later -- see that generator's own docstring
                # for the full reasoning.
                supplier_code=generate_unique_supplier_code(),
            )
            db.session.add(profile)
            db.session.flush()
        return profile

    @staticmethod
    def update(profile: SupplierProfile, **fields) -> SupplierProfile:
        """The first real write path for a supplier's own profile --
        every field this domain currently supports editing (business
        details, photo visibility, and the three contact channels) all
        go through this one method, matching update_my_profile's own
        docstring on why this deliberately isn't split into a narrow
        "just the new fields" endpoint plus a separate one for the
        older mock-only ones. Silently ignores an unrecognised kwarg
        rather than raising -- the service layer is responsible for
        only ever passing real column names; this method's own job is
        applying them and committing once, not validating shape."""
        for key, value in fields.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        db.session.commit()
        return profile

    @staticmethod
    def search_by_name_prefix(name_query: str, limit: int = 20) -> List[SupplierProfile]:
        """Case-insensitive PREFIX match only -- see module docstring.
        `name_query` should already be caller-trimmed; this method
        escapes SQL LIKE's own special characters (%, _) in it before
        building the pattern, so someone searching a literal "%" or a
        name containing "_" gets a real narrow match instead of an
        unintended wildcard scan -- see escape_like_pattern's own
        docstring for the full reasoning."""
        from src.shared.validation.identifiers import escape_like_pattern

        pattern = f"{escape_like_pattern(name_query)}%"
        return (
            SupplierProfile.query.filter(
                SupplierProfile.business_name.ilike(pattern, escape="\\"),
                SupplierProfile.is_deleted.is_(False),
            )
            .order_by(SupplierProfile.business_name.asc())
            .limit(limit)
            .all()
        )
