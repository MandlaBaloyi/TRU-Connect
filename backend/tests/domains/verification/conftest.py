"""
Verification test fixtures.

make_supplier / make_supplier_profile are COPIED from
network/connections/conftest.py rather than imported, matching this
codebase's own convention -- orders, notifications, bulk_import and
every supplier sub-domain each carry their own copy, and the
connections conftest's docstring explains why.

ONE DIFFERENCE WORTH KNOWING: make_supplier here produces a VERIFIED
supplier, like everywhere else. The tests in this package that need a
HIDDEN one build it explicitly through make_hidden_supplier, because
being invisible is the thing under test rather than the backdrop.
"""
from __future__ import annotations

import pytest

from src.extensions import db


@pytest.fixture()
def make_supplier(make_user, db_session):
    from src.domains.auth.models.user import UserRole, VerificationStatus
    from src.domains.supplier.supplier_profile.models.supplier_profile import (
        SupplierVerificationStatus,
    )
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    def _make(email: str = "supplier@example.com"):
        user = make_user(email, role=UserRole.SUPPLIER, verification_status=VerificationStatus.VERIFIED)
        db_session.commit()
        # Mirrors OTPService._seed_supplier_profile — see module docstring.
        profile = SupplierProfileRepository.get_or_create_for_supplier(
            user.id, default_name=user.first_name or ""
        )
        # VERIFIED, because this fixture means "a supplier a business
        # can actually trade with". Since V2_12 Phase 1 an UNVERIFIED
        # supplier is INVISIBLE to buyers -- the curtain -- so leaving
        # the model's own default would make every business-facing test
        # assert against a supplier nobody can see, and they would fail
        # for a reason that has nothing to do with what they test.
        # A test that wants the curtain CLOSED says so explicitly.
        profile.verification_status = SupplierVerificationStatus.VERIFIED
        db_session.commit()
        return user

    return _make


@pytest.fixture()
def make_supplier_profile(db_session):
    """Factory for a SupplierProfile tied to a real supplier User.
    Callers pass a supplier User (from make_supplier) and get back a
    real, committed SupplierProfile row with sensible defaults,
    overridable per test.

    IDEMPOTENT via get_or_create_for_supplier, NOT a raw insert --
    make_supplier already seeds a bare profile for every supplier it
    creates (see that fixture's own docstring), so a plain INSERT here
    would collide with uq_supplier_profiles_supplier_id. This fetches
    that already-seeded row and applies the caller's overrides onto it
    instead, which also matches how the real system actually works:
    the profile exists from verification onward, and gets filled in
    with real details afterward, not created fresh at that point.
    """
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierVerificationStatus
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    def _make(supplier_user, *, business_name: str = "Test Wholesale", **overrides):
        profile = SupplierProfileRepository.get_or_create_for_supplier(supplier_user.id, default_name=business_name)
        profile.business_name = business_name
        profile.verification_status = overrides.pop("verification_status", SupplierVerificationStatus.VERIFIED)
        for field, value in overrides.items():
            setattr(profile, field, value)
        db.session.commit()
        return profile

    return _make
