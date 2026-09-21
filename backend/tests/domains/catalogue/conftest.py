"""
Catalogue test fixtures.

make_supplier/make_supplier_profile mirror the copies in
supplier/inventory/conftest.py and network/connections/conftest.py
exactly. Duplicated rather than imported cross-domain, matching how
every other domain's conftest carries its own copy instead of reaching
for one shared global fixture module.
"""
from __future__ import annotations

import pytest

from src.extensions import db


@pytest.fixture()
def make_business(make_user, db_session):
    """A verified business, for the browse's "my suppliers" filter.

    BUILT HERE BECAUSE FIXTURES ARE PER-PACKAGE IN THIS SUITE. The
    network conftests each carry their own copy of this factory; adding
    a fifth beside them is the convention rather than an oversight. If
    it is ever hoisted to a shared conftest, hoist all of them together.
    """
    from src.domains.auth.models.user import UserRole, VerificationStatus

    def _make(email: str = "browse-buyer@example.com"):
        user = make_user(
            email, role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED
        )
        db_session.commit()
        return user

    return _make


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
