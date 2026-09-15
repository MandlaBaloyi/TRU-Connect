"""
Supplier profile auto-seeding tests -- confirms the real end-to-end
chain proven manually in this session: a supplier is NOT searchable
before verifying their email, and becomes searchable immediately after,
with zero manual seeding required.

Drives everything through the real HTTP routes (client.post), matching
test_auth.py's own approach, since the actual behaviour being tested
IS the interaction between /auth/register, /auth/phone/verify-otp, and
Supplier Discovery -- not just the seeding function in isolation.
"""
from __future__ import annotations

import re

import pytest

from src.shared.email.email import get_fake_provider


def _register_supplier(
    client, *, owner_name="Sipho Mahlangu", business_name="Mahlangu Fresh Produce", email="sipho@example.com"
):
    body = {
        "role": "supplier",
        "businessName": business_name,
        "email": email,
        "password": "Abcd1234!",
        "confirmPassword": "Abcd1234!",
        "acceptTerms": True,
    }
    # owner name is optional now -- only send it when the test supplies one
    if owner_name is not None:
        body["ownerName"] = owner_name
    return client.post("/api/v1/auth/register", json=body)


def _extract_otp(email: str) -> str:
    for sent in get_fake_provider().sent_emails:
        if sent["to"] == email and sent["subject"] == "Your TruConnect verification code":
            match = re.search(r"letter-spacing:6px[^>]*>\s*(\d{6})", sent["html_body"])
            if match:
                return match.group(1)
    raise AssertionError(f"No OTP email found for {email}")


def test_supplier_not_searchable_before_verification(client, make_user):
    from src.domains.auth.models.user import UserRole, VerificationStatus
    from src.domains.network.connections.services import (
        discovery_service,
    )
    from src.extensions import db

    response = _register_supplier(client, owner_name="Not Yet Verified", email="notyet@example.com")
    assert response.status_code == 201

    viewer_business = make_user(
        "seeding-viewer-1@example.com", role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED
    )
    db.session.commit()

    results = discovery_service.search_suppliers("Not Yet Verified", viewer_business.id)
    assert results == []


def test_email_verification_seeds_the_profile_but_does_not_make_them_sellable(client, make_user):
    """THIS TEST USED TO ASSERT THE OPPOSITE, and the change is the
    point rather than a regression.

    It was called "becomes searchable IMMEDIATELY after verification",
    written when OTP verification was the only gate a supplier had.
    V2_12 Phase 1 introduced a second, separate one: confirming your
    EMAIL proves you own an address, and says nothing about whether
    you are a real business somebody should send money to. Those are
    two different questions and auth.users.verification_status /
    SupplierProfile.verification_status are two different columns.

    So the profile is seeded and complete -- with the BUSINESS name,
    which is what this test has always really been protecting -- and
    the supplier is INVISIBLE until a human approves them.
    """
    from src.domains.auth.models.user import UserRole, VerificationStatus
    from src.domains.network.connections.services import discovery_service
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )
    from src.extensions import db

    response = _register_supplier(client, owner_name="Sipho Mahlangu", email="sipho-seed@example.com")
    assert response.status_code == 201

    code = _extract_otp("sipho-seed@example.com")
    verify_response = client.post(
        "/api/v1/auth/phone/verify-otp",
        json={"destination": "sipho-seed@example.com", "code": code},
    )
    assert verify_response.status_code == 200

    viewer_business = make_user(
        "seeding-viewer-2@example.com", role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED
    )
    db.session.commit()

    # THE PROFILE IS REAL AND CORRECTLY NAMED. Seeded with the BUSINESS
    # name (mandatory at registration), not the owner name -- see
    # otp_service._seed_supplier_profile.
    from src.domains.auth.repositories.user_repository import UserRepository

    supplier_user = UserRepository.get_by_email("sipho-seed@example.com")
    profile = SupplierProfileRepository.get_by_supplier_id(supplier_user.id)
    assert profile is not None
    assert profile.business_name == "Mahlangu Fresh Produce"

    # AND NOBODY CAN SEE THEM. The curtain.
    assert discovery_service.search_suppliers("Mahlangu Fresh Produce", viewer_business.id) == []


def test_the_supplier_appears_the_moment_a_human_approves_them(client, make_user):
    """The other half: the curtain opens, and everything the supplier
    built while waiting becomes visible at once."""
    from src.domains.auth.models.user import UserRole, VerificationStatus
    from src.domains.auth.repositories.user_repository import UserRepository
    from src.domains.network.connections.services import discovery_service
    from src.domains.verification.services import verification_service
    from src.extensions import db

    _register_supplier(client, owner_name="Sipho Mahlangu", email="sipho-approve@example.com")
    code = _extract_otp("sipho-approve@example.com")
    client.post(
        "/api/v1/auth/phone/verify-otp",
        json={"destination": "sipho-approve@example.com", "code": code},
    )

    viewer_business = make_user(
        "seeding-viewer-3@example.com", role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED
    )
    staff = make_user(
        "seeding-staff@example.com", role=UserRole.ADMIN, verification_status=VerificationStatus.VERIFIED
    )
    db.session.commit()

    supplier_user = UserRepository.get_by_email("sipho-approve@example.com")
    verification_service.approve(
        supplier_user.id, decided_by_user_id=str(staff.id), reason="Checked during onboarding."
    )

    results = discovery_service.search_suppliers("Mahlangu Fresh Produce", viewer_business.id)
    assert len(results) == 1
    assert results[0]["businessName"] == "Mahlangu Fresh Produce"


def test_supplier_registration_requires_a_valid_business_name(client):
    """Business name is mandatory and shape-checked
    (shared.validation.business_name) -- a missing or junk name is a
    422, never a silently-accepted profile."""
    missing = client.post(
        "/api/v1/auth/register",
        json={
            "role": "supplier",
            "ownerName": "Someone",
            "email": "noname@example.com",
            "password": "Abcd1234!",
            "confirmPassword": "Abcd1234!",
            "acceptTerms": True,
        },
    )
    assert missing.status_code == 422

    for bad in ("a", "aaaa", "1234"):
        response = _register_supplier(
            client, business_name=bad, email=f"bad-{bad}@example.com"
        )
        assert response.status_code == 422, bad


def test_supplier_registration_succeeds_without_an_owner_name(client):
    """Owner name is optional now -- a sole trader with just a business
    name registers fine, and the profile seeds from the business name."""
    response = _register_supplier(
        client, owner_name=None, business_name="Solo Trader Supplies", email="solo@example.com"
    )
    assert response.status_code == 201

    code = _extract_otp("solo@example.com")
    verify = client.post(
        "/api/v1/auth/phone/verify-otp", json={"destination": "solo@example.com", "code": code}
    )
    assert verify.status_code == 200

    from src.domains.auth.models.user import User
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    user = User.query.filter_by(email="solo@example.com").first()
    assert user.first_name is None
    profile = SupplierProfileRepository.get_by_supplier_id(user.id)
    assert profile is not None
    assert profile.business_name == "Solo Trader Supplies"


def test_get_or_create_is_idempotent(client, db_session):
    """The actual mechanism was_already_verified relies on: calling
    get_or_create_for_supplier twice for the same supplier must never
    create a second row -- confirmed directly at the repository layer,
    the same way test_connection_requests.py tests double-request
    idempotency directly rather than simulating a literal double-tap
    over HTTP."""
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )
    from src.domains.auth.models.user import User

    response = _register_supplier(client, owner_name="Idempotent Test", email="idempotent@example.com")
    assert response.status_code == 201
    code = _extract_otp("idempotent@example.com")
    client.post("/api/v1/auth/phone/verify-otp", json={"destination": "idempotent@example.com", "code": code})

    user = User.query.filter_by(email="idempotent@example.com").first()

    SupplierProfileRepository.get_or_create_for_supplier(user.id, default_name="Should not be used")
    SupplierProfileRepository.get_or_create_for_supplier(user.id, default_name="Also should not be used")

    count = SupplierProfile.query.filter_by(supplier_id=user.id).count()
    assert count == 1


def _register_business(
    client,
    *,
    first_name="Thabo",
    last_name="Nkosi",
    email="thabo@example.com",
    business_name="Nkosi Spaza",
):
    return client.post(
        "/api/v1/auth/register",
        json={
            "role": "business",
            "firstName": first_name,
            "lastName": last_name,
            "businessName": business_name,
            "email": email,
            "password": "Abcd1234!",
            "confirmPassword": "Abcd1234!",
            "acceptPrivacyPolicy": True,
        },
    )


def test_business_profile_seeded_with_real_name_at_verification(client):
    """Symmetric with the supplier tests above -- discovered while
    testing Supplier Approval end-to-end: a business that never opens
    My Business had no BusinessProfile row either (that domain's own
    get_or_create_for_business is ALSO lazy-only), so a supplier
    reviewing an incoming connection request saw "Unknown business"
    instead of a real name. Same fix (_seed_business_profile), same
    reasoning as the supplier side.

    THIS USED TO ASSERT "Thabo Nkosi" -- THE OWNER'S OWN NAME. That was
    the bug rather than the behaviour: registration collected
    businessName and never stored it, so the seed fell through to
    firstName + lastName and every shop on the platform was listed
    under the person who signed it up. A supplier looking their own
    customer up in Find Business saw a human name where a shop should
    be. Both roles now carry the name on users.business_name from
    registration.
    """
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )
    from src.domains.auth.models.user import User

    response = _register_business(
        client,
        first_name="Thabo",
        last_name="Nkosi",
        email="thabo-seed@example.com",
        business_name="Nkosi Corner Store",
    )
    assert response.status_code == 201
    code = _extract_otp("thabo-seed@example.com")
    verify_response = client.post(
        "/api/v1/auth/phone/verify-otp", json={"destination": "thabo-seed@example.com", "code": code}
    )
    assert verify_response.status_code == 200

    user = User.query.filter_by(email="thabo-seed@example.com").first()
    profile = BusinessProfileRepository.get_for_business(user.id)
    assert profile is not None
    assert profile.business_name == "Nkosi Corner Store"
    assert profile.business_name != "Thabo Nkosi", "the shop is not the shopkeeper"


@pytest.mark.parametrize(
    "bad_name",
    [
        pytest.param("a", id="too-short"),
        pytest.param("aaaa", id="one-character-repeated"),
        pytest.param("1234", id="no-letter"),
        pytest.param("N" * 60, id="too-long"),
    ],
)
def test_a_business_name_must_be_a_real_name(client, bad_name):
    """Same validator as the supplier side (shared.validation.
    business_name), so the two roles cannot drift into having different
    ideas of a usable name."""
    response = _register_business(
        client, email=f"badname-{len(bad_name)}-{bad_name[:2]}@example.com", business_name=bad_name
    )

    # 422, not 400 -- this route reports schema failures as
    # "Validation failed" with a 422, which is the shape every
    # registration error already has.
    assert response.status_code == 422


def test_a_business_cannot_register_without_a_business_name(client):
    """It is the name every business-facing screen shows. Optional was
    the old behaviour and it is what produced the owner-name bug."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "role": "business",
            "firstName": "Thabo",
            "lastName": "Nkosi",
            "email": "business-noname@example.com",
            "password": "Abcd1234!",
            "confirmPassword": "Abcd1234!",
            "acceptPrivacyPolicy": True,
        },
    )

    assert response.status_code == 422
