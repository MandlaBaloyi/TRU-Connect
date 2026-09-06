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
        if sent["to"] == email and sent["subject"] == "Your TRU Connect verification code":
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


def test_supplier_becomes_searchable_immediately_after_verification(client, make_user):
    from src.domains.auth.models.user import UserRole, VerificationStatus
    from src.domains.network.connections.services import discovery_service
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

    # Seeded with the BUSINESS name now (mandatory field), not the
    # owner name -- see otp_service._seed_supplier_profile.
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


def _register_business(client, *, first_name="Thabo", last_name="Nkosi", email="thabo@example.com"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "role": "business",
            "firstName": first_name,
            "lastName": last_name,
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
    placeholder-name reasoning as the supplier side."""
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )
    from src.domains.auth.models.user import User

    response = _register_business(client, first_name="Thabo", last_name="Nkosi", email="thabo-seed@example.com")
    assert response.status_code == 201
    code = _extract_otp("thabo-seed@example.com")
    verify_response = client.post(
        "/api/v1/auth/phone/verify-otp", json={"destination": "thabo-seed@example.com", "code": code}
    )
    assert verify_response.status_code == 200

    user = User.query.filter_by(email="thabo-seed@example.com").first()
    profile = BusinessProfileRepository.get_for_business(user.id)
    assert profile is not None
    assert profile.business_name == "Thabo Nkosi"
