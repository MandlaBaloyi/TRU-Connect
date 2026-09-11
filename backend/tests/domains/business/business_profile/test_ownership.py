"""
Business Profile ownership + correctness tests.

THE OWNERSHIP SHAPE HERE IS DIFFERENT FROM LOAN BOOK/ORDER BOOK, ON
PURPOSE: there is no id-based lookup route at all (no
GET /business-profile/<id>) -- every route resolves the profile
entirely from get_jwt_identity(), never from anything in the URL or
body. That removes the classic IDOR surface (an attacker guessing/
enumerating another business's id) structurally, not just via a
repository filter check. What's actually worth testing here is the
weaker-but-still-real property: business A's writes never leak into or
overwrite business B's profile, and each business always gets back
their OWN profile, never someone else's.
"""
from __future__ import annotations

import uuid

from flask_jwt_extended import create_access_token

from src.domains.business.business_profile.repositories.business_profile_repository import (
    BusinessProfileRepository,
)
from src.domains.business.business_profile.services.business_profile_service import BusinessProfileService


class TestGetOrCreate:
    def test_first_access_creates_an_empty_profile(self, app, make_business_user):
        business = make_business_user("first-access@example.com")
        with app.app_context():
            profile = BusinessProfileService.get_profile(business.id)
        assert profile["businessDetails"]["businessName"] == ""
        assert profile["tradingDetails"]["products"] == []

    def test_second_access_returns_the_same_row_not_a_new_one(self, app, make_business_user):
        business = make_business_user("second-access@example.com")
        with app.app_context():
            first = BusinessProfileService.get_profile(business.id)
            second = BusinessProfileService.get_profile(business.id)
        assert first["id"] == second["id"]


class TestContactDetailsLiveOverlay:
    def test_same_as_account_reflects_live_user_phone_not_a_stale_copy(self, app, make_business_user, db_session):
        business = make_business_user("live-overlay@example.com", phone="0821111111")
        with app.app_context():
            profile = BusinessProfileService.get_profile(business.id)
            assert profile["contactDetails"]["phone"] == "0821111111"
            assert profile["contactDetails"]["usesSameAsAccountPhone"] is True

            # Change the ACCOUNT's phone directly -- the profile's
            # "same as account" value must follow automatically.
            from src.domains.auth.models.user import User
            user = User.query.get(business.id)
            user.phone_number = "0829999999"
            db_session.commit()

            refreshed = BusinessProfileService.get_profile(business.id)
        assert refreshed["contactDetails"]["phone"] == "0829999999"


class TestVerificationDerivedFromRealSignal:
    def test_phone_verified_reflects_real_user_verification_status(self, app, db_session):
        from src.domains.auth.models.user import User, UserRole, VerificationStatus

        unverified = User(
            id=uuid.uuid4(), email="unverified@example.com", password_hash="x",
            role=UserRole.BUSINESS, verification_status=VerificationStatus.UNVERIFIED,
        )
        db_session.add(unverified)
        db_session.commit()

        with app.app_context():
            profile = BusinessProfileService.get_profile(unverified.id)
        assert profile["verification"]["phoneVerified"] is False
        # Honest, not faked: no email-verification flow exists in this
        # backend yet.
        assert profile["verification"]["emailVerified"] is False


class TestSectionOwnershipIsolation:
    def test_business_a_update_never_touches_business_bs_profile(self, app, make_business_user):
        business_a = make_business_user("owner-a@example.com")
        business_b = make_business_user("owner-b@example.com")

        with app.app_context():
            BusinessProfileService.update_business_details(business_a.id, {"businessName": "A's Shop"})
            BusinessProfileService.update_business_details(business_b.id, {"businessName": "B's Shop"})

            profile_a = BusinessProfileService.get_profile(business_a.id)
            profile_b = BusinessProfileService.get_profile(business_b.id)

        assert profile_a["businessDetails"]["businessName"] == "A's Shop"
        assert profile_b["businessDetails"]["businessName"] == "B's Shop"
        assert profile_a["id"] != profile_b["id"]

    def test_repository_get_for_business_never_returns_another_businesss_row(self, app, make_business_user):
        business_a = make_business_user("repo-a@example.com")
        business_b = make_business_user("repo-b@example.com")

        with app.app_context():
            BusinessProfileRepository.get_or_create_for_business(business_a.id)
            BusinessProfileRepository.get_or_create_for_business(business_b.id)

            row_for_a = BusinessProfileRepository.get_for_business(business_a.id)
            row_for_b = BusinessProfileRepository.get_for_business(business_b.id)

        assert row_for_a.business_id == business_a.id
        assert row_for_b.business_id == business_b.id
        assert row_for_a.id != row_for_b.id


class TestUpdateEachSectionIndependently:
    def test_updating_one_section_never_clobbers_another(self, app, make_business_user):
        business = make_business_user("independent-sections@example.com")
        with app.app_context():
            BusinessProfileService.update_business_details(business.id, {"businessName": "Test Shop"})
            BusinessProfileService.update_location(business.id, {"cityOrTown": "Johannesburg"})
            profile = BusinessProfileService.get_profile(business.id)

        assert profile["businessDetails"]["businessName"] == "Test Shop"
        assert profile["location"]["cityOrTown"] == "Johannesburg"

    def test_empty_business_name_is_rejected(self, app, make_business_user):
        from src.domains.business.business_profile.services.errors import BusinessProfileValidationError
        import pytest

        business = make_business_user("empty-name@example.com")
        with app.app_context(), pytest.raises(BusinessProfileValidationError):
            BusinessProfileService.update_business_details(business.id, {"businessName": "   "})


class TestApiOwnership:
    """HTTP-level: two businesses, real JWTs, confirm each only ever
    sees/edits their own profile through the actual routes."""

    def test_get_returns_only_the_authenticated_businesss_profile(self, app, client, make_business_user):
        business_a = make_business_user("api-a@example.com")
        business_b = make_business_user("api-b@example.com")

        with app.app_context():
            token_a = create_access_token(
                identity=str(business_a.id), additional_claims={"role": "business"}
            )
            token_b = create_access_token(
                identity=str(business_b.id), additional_claims={"role": "business"}
            )

        client.patch(
            "/api/v1/business-profile/business-details",
            json={"businessName": "A via API"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        client.patch(
            "/api/v1/business-profile/business-details",
            json={"businessName": "B via API"},
            headers={"Authorization": f"Bearer {token_b}"},
        )

        response_a = client.get("/api/v1/business-profile", headers={"Authorization": f"Bearer {token_a}"})
        response_b = client.get("/api/v1/business-profile", headers={"Authorization": f"Bearer {token_b}"})

        assert response_a.get_json()["data"]["businessDetails"]["businessName"] == "A via API"
        assert response_b.get_json()["data"]["businessDetails"]["businessName"] == "B via API"

    def test_unauthenticated_request_is_rejected(self, client):
        response = client.get("/api/v1/business-profile")
        assert response.status_code == 401

    def test_invalid_category_is_rejected_with_422(self, app, client, make_business_user):
        business = make_business_user("invalid-category@example.com")
        with app.app_context():
            token = create_access_token(
                identity=str(business.id), additional_claims={"role": "business"}
            )

        response = client.patch(
            "/api/v1/business-profile/business-details",
            json={"category": "NOT_A_REAL_CATEGORY"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
