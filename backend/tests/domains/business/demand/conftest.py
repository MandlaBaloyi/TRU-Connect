"""Demand engine test fixtures.

Same shape as business_profile's and order_book's own conftests -- the
real create_app("testing") factory and a VERIFIED business user, since
fully_authenticated re-checks status against the database on every
request.

make_business RATHER THAN make_business_user, to match the name the
network and community suites use: these tests exercise the same feed
sections those do, and one concept with two fixture names is how a
test file ends up importing the wrong one.
"""
from __future__ import annotations

import uuid

import pytest

from src import create_app
from src.extensions import db


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def db_session(app):
    return db.session


@pytest.fixture()
def client(app):
    """Added for the setup-state route tests. The rest of this suite
    calls services directly, but a route's ROLE PIN can only be proven
    over HTTP -- calling the service reaches straight past the
    decorator that is the thing under test."""
    return app.test_client()


@pytest.fixture()
def make_supplier(db_session):
    """A verified supplier user, with a bare profile seeded the way
    OTPService._seed_supplier_profile does it.

    IT USED TO SKIP THE PROFILE, back when the only supplier in this
    suite existed to be REFUSED by a role decorator and never reached
    anything that needed one. The stock_collection tests need suppliers a
    business can actually see, so it now mirrors the network and
    community conftests' own fixture of the same name -- one concept
    with two behaviours under one name is how a test file ends up
    asserting against a supplier that does not exist.
    """
    from src.domains.auth.models.user import User, UserRole, VerificationStatus
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    def _make(email: str = "supplier@example.com"):
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash="x",
            role=UserRole.SUPPLIER,
            verification_status=VerificationStatus.VERIFIED,
        )
        db_session.add(user)
        db_session.commit()
        SupplierProfileRepository.get_or_create_for_supplier(user.id, default_name="")
        db_session.commit()
        return user

    return _make


@pytest.fixture()
def make_supplier_profile(db_session):
    """Fills in an already-seeded SupplierProfile. Mirrors the network
    and community conftests exactly -- get_or_create rather than a raw
    insert, because make_supplier above has already created the row and
    an INSERT would collide with uq_supplier_profiles_supplier_id.

    VERIFIED BY DEFAULT, because every business-facing test means "a
    supplier a shop can actually trade with"; since the curtain, an
    UNVERIFIED supplier is invisible and the assertion would fail for a
    reason unrelated to what is being tested.
    """
    from src.domains.supplier.supplier_profile.models.supplier_profile import (
        SupplierVerificationStatus,
    )
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    def _make(supplier_user, *, business_name: str = "Test Wholesale", **overrides):
        profile = SupplierProfileRepository.get_or_create_for_supplier(
            supplier_user.id, default_name=business_name
        )
        profile.business_name = business_name
        profile.verification_status = overrides.pop(
            "verification_status", SupplierVerificationStatus.VERIFIED
        )
        for field, value in overrides.items():
            setattr(profile, field, value)
        db_session.commit()
        return profile

    return _make


@pytest.fixture()
def make_business(db_session):
    from src.domains.auth.models.user import User, UserRole, VerificationStatus

    def _make(email: str, phone: str = "0821234567"):
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash="x",
            role=UserRole.BUSINESS,
            verification_status=VerificationStatus.VERIFIED,
            phone_number=phone,
        )
        db_session.add(user)
        db_session.commit()
        return user

    return _make
