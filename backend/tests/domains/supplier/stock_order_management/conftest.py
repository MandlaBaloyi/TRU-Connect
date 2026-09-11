"""
Stock Order Management test fixtures -- copied from
tests/domains/network/orders/conftest.py's own identical fixtures
(all genuinely generic identity/connection factories, not orders-
specific, so reusing them here is the same "no reason to reinvent"
reasoning already applied to platform/notifications' own conftest).

Builds on tests/conftest.py's `app`/`client`/`db_session`/`make_user` --
does NOT redefine `app`/`client`/`db_session` locally the way loan_book's
own conftest.py does. Per the root conftest's own docstring, that local
pattern predates this domain's promotion to a shared root fixture set;
new domains use the root one directly.

make_user's default verification_status is UNVERIFIED (the model's own
default) -- every factory below explicitly overrides it to VERIFIED so
@fully_authenticated (which re-checks the database, not the token) lets
these users through, matching loan_book/conftest.py's own
make_business_user's identical override for the identical reason.

make_supplier ALSO seeds a companion SupplierProfile -- discovered as a
real gap while testing Customer Requests: this fixture creates a User
directly, bypassing the real registration+OTP-verification flow where
OTPService._seed_supplier_profile actually runs (auth/services/
otp_service.py). Without mirroring that seed here too, every supplier
built by this fixture would violate the invariant the service layer
correctly assumes (get_customer_requests/approve_request/etc. all call
_resolve_supplier_profile_id, which raises SupplierNotFoundError if no
profile exists) -- a real production account can never reach that
state, but a fixture that skips the seed step easily can.
"""
from __future__ import annotations

import pytest

from src.extensions import db


@pytest.fixture()
def make_business(make_user, db_session):
    from src.domains.auth.models.user import UserRole, VerificationStatus

    def _make(email: str = "business@example.com"):
        user = make_user(email, role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED)
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


@pytest.fixture()
def make_business_profile(db_session):
    """Factory for a BusinessProfile tied to a real business User —
    the mirror of make_supplier_profile, added for Find Business
    (the reverse search direction). Same get_or_create-then-override
    pattern for the same reason: real accounts get this seeded
    automatically at verification (OTPService._seed_business_profile),
    so this fixture mirrors that rather than raw-inserting."""
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    def _make(business_user, *, business_name: str = "Test Business", **overrides):
        profile = BusinessProfileRepository.get_or_create_for_business(business_user.id, default_name=business_name)
        profile.business_name = business_name
        for field, value in overrides.items():
            setattr(profile, field, value)
        db.session.commit()
        return profile

    return _make


@pytest.fixture()
def make_active_connection(db_session):
    """THE REAL, MISSING PRECONDITION most existing checkout tests
    never needed until now -- confirmed after direct report:
    submit_checkout never actually verified an active connection
    existed at all. Every test that submits a real checkout now needs
    one established first; this fixture is the one, reusable way to
    do that (request + immediate approval), rather than repeating the
    same two-call sequence in every affected test."""
    from src.domains.network.connections.repositories.connection_request_repository import (
        ConnectionRequestRepository,
    )
    from src.domains.network.connections.services import (
        request_service,
    )

    def _make(business, supplier_profile):
        request_service.request_connection(business.id, supplier_profile.id)
        request = ConnectionRequestRepository.get_for_business_and_supplier(business.id, supplier_profile.id)
        request_service.approve_request(supplier_profile.supplier_id, request.id)
        return request

    return _make
