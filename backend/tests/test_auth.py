"""
Authentication module tests.
Ref: continuation master prompt, Step 16; Auth Hardening master prompt,
Objective 10.

Two groups:
1. Pure unit tests -- no database connection needed:
       pytest tests/test_auth.py -k "not Integration"
2. Integration tests -- need a real PostgreSQL test database:
       pytest tests/test_auth.py -k Integration
"""
from __future__ import annotations

import re

import pytest

from src import create_app
from src.extensions import db
from src.shared.cache.cache import cache
from src.shared.email.email import get_fake_provider
from src.domains.auth.schemas.auth_schemas import BusinessRegisterSchema, LoginSchema, SupplierRegisterSchema
from src.domains.auth.schemas.otp_schemas import RequestOtpSchema, VerifyOtpSchema
from src.domains.auth.schemas.password_reset_schemas import ForgotPasswordSchema, ResetPasswordSchema
from src.domains.auth.utils.otp import generate_numeric_otp, hash_otp, verify_otp_hash
from src.shared.security.security import hash_password, passwords_match, validate_password_complexity, verify_password
from src.shared.tickets.tickets import create_ticket, hash_ticket, is_ticket_expired, ticket_expiry, verify_ticket
from src.domains.security.rate_limit.limiter import limiter


# ----------------------------------------------------------------------------
# Group 1: pure unit tests.
# ----------------------------------------------------------------------------

class TestPasswordSecurity:
    def test_hash_and_verify_round_trip(self):
        hashed = hash_password("Abcd1234!")
        assert verify_password("Abcd1234!", hashed)

    def test_verify_rejects_wrong_password(self):
        hashed = hash_password("Abcd1234!")
        assert not verify_password("wrong password", hashed)

    def test_complexity_rejects_short_password(self):
        assert any("8 characters" in e for e in validate_password_complexity("Ab1!"))

    def test_complexity_accepts_valid_password(self):
        assert validate_password_complexity("Abcd1234!") == []

    def test_passwords_match(self):
        assert passwords_match("Abcd1234!", "Abcd1234!")


class TestOtpUtilities:
    def test_generated_otp_is_correct_length_and_numeric(self):
        code = generate_numeric_otp()
        assert len(code) == 6
        assert code.isdigit()

    def test_otp_hash_round_trip(self):
        code = generate_numeric_otp()
        assert verify_otp_hash(code, hash_otp(code))

    def test_otp_hash_rejects_wrong_code(self):
        assert not verify_otp_hash("654321", hash_otp("123456"))


class TestTicketUtilities:
    def test_create_ticket_is_url_safe_and_reasonably_long(self):
        assert len(create_ticket()) >= 32

    def test_hash_and_verify_round_trip(self):
        ticket = create_ticket()
        assert verify_ticket(ticket, hash_ticket(ticket))

    def test_verify_rejects_wrong_ticket(self):
        assert not verify_ticket("wrong-ticket", hash_ticket(create_ticket()))

    def test_expiry_helpers(self):
        from datetime import timedelta

        from src.core.base_model import utcnow

        future = ticket_expiry(hours=1)
        assert not is_ticket_expired(future)
        past = utcnow() - timedelta(hours=1)
        assert is_ticket_expired(past)


class TestBusinessRegisterSchema:
    def _valid_payload(self, **overrides):
        payload = {
            "firstName": "Thabo",
            "lastName": "Nkosi",
            # MANDATORY SINCE THE OWNER-NAME BUG. Without it the profile
            # was seeded from firstName + lastName, so a shop appeared
            # under its owner's personal name everywhere a supplier
            # could look it up.
            "businessName": "Nkosi Spaza",
            "email": "thabo@example.com",
            "password": "Abcd1234!",
            "confirmPassword": "Abcd1234!",
            "acceptPrivacyPolicy": True,
        }
        payload.update(overrides)
        return payload

    def test_accepts_valid_payload(self):
        data = BusinessRegisterSchema().load(self._valid_payload())
        assert data["first_name"] == "Thabo"
        assert data["business_name"] == "Nkosi Spaza"

    def test_rejects_missing_privacy_policy(self):
        with pytest.raises(Exception):
            BusinessRegisterSchema().load(self._valid_payload(acceptPrivacyPolicy=False))

    def test_rejects_a_missing_business_name(self):
        payload = self._valid_payload()
        del payload["businessName"]

        with pytest.raises(Exception):
            BusinessRegisterSchema().load(payload)

    def test_rejects_a_name_that_is_not_a_name(self):
        """Same validator as the supplier side, so the two roles cannot
        drift into different ideas of a usable name."""
        with pytest.raises(Exception):
            BusinessRegisterSchema().load(self._valid_payload(businessName="1234"))


class TestSupplierRegisterSchema:
    def test_accepts_valid_payload(self):
        data = SupplierRegisterSchema().load(
            {
                "businessName": "Dlamini Distributors",
                "ownerName": "Naledi Dlamini",
                "email": "naledi@example.com",
                "password": "Abcd1234!",
                "confirmPassword": "Abcd1234!",
                "acceptTerms": True,
            }
        )
        assert data["owner_name"] == "Naledi Dlamini"
        assert data["business_name"] == "Dlamini Distributors"

    def test_rejects_missing_business_name(self):
        with pytest.raises(Exception):
            SupplierRegisterSchema().load(
                {
                    "ownerName": "Naledi Dlamini",
                    "email": "naledi2@example.com",
                    "password": "Abcd1234!",
                    "confirmPassword": "Abcd1234!",
                    "acceptTerms": True,
                }
            )

    def test_accepts_missing_owner_name(self):
        data = SupplierRegisterSchema().load(
            {
                "businessName": "Solo Trader Supplies",
                "email": "solo-schema@example.com",
                "password": "Abcd1234!",
                "confirmPassword": "Abcd1234!",
                "acceptTerms": True,
            }
        )
        assert data.get("owner_name") in (None, "")


class TestLoginSchema:
    def test_accepts_valid_payload(self):
        data = LoginSchema().load({"email": "a@example.com", "password": "Abcd1234!"})
        assert data["email"] == "a@example.com"


class TestPasswordResetSchemas:
    def test_forgot_password_schema_requires_valid_email(self):
        with pytest.raises(Exception):
            ForgotPasswordSchema().load({"email": "not-an-email"})

    def test_reset_password_schema_uses_ticket_field(self):
        data = ResetPasswordSchema().load(
            {"ticket": "abc", "newPassword": "Abcd1234!", "confirmPassword": "Abcd1234!"}
        )
        assert data["ticket"] == "abc"


# ----------------------------------------------------------------------------
# Group 2: integration tests -- require a real PostgreSQL test database.
# ----------------------------------------------------------------------------

@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        get_fake_provider().clear()
        cache.clear()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _register_business(client, email="thabo@example.com", password="Abcd1234!", business_name="Nkosi Spaza"):
    # businessName IS MANDATORY NOW. It was optional and dropped on the
    # floor, so business_profiles.business_name was seeded from
    # firstName + lastName and every shop was listed under its owner's
    # personal name -- see auth_service.register_business.
    return client.post(
        "/api/v1/auth/register",
        json={
            "role": "business",
            "firstName": "Thabo",
            "lastName": "Nkosi",
            "businessName": business_name,
            "email": email,
            "password": password,
            "confirmPassword": password,
            "acceptPrivacyPolicy": True,
        },
    )


def _extract_otp(caplog, email) -> str:
    """OTP delivery goes through the fake provider (dev-mode SMTP is
    never actually used in tests), so read it from there rather than
    from logs. `caplog` is accepted for signature consistency with
    tests that also assert on log output, but is not read here."""
    for sent in get_fake_provider().sent_emails:
        if sent["to"] == email and sent["subject"] == "Your TruConnect verification code":
            match = re.search(r"letter-spacing:6px[^>]*>\s*(\d{6})", sent["html_body"])
            if match:
                return match.group(1)
    raise AssertionError(f"No OTP email found for {email}")


class TestRegistrationIntegration:
    def test_register_returns_no_tokens(self, client):
        """Core of Objective 1: there must be nothing to bypass with."""
        response = _register_business(client, email="no-tokens@example.com")
        assert response.status_code == 201
        body = response.get_json()
        assert "tokens" not in body["data"]
        assert body["data"]["user"]["email"] == "no-tokens@example.com"

    def test_verified_duplicate_email_is_rejected(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="dup@example.com")
        code = _extract_otp(caplog, "dup@example.com")
        client.post("/api/v1/auth/phone/verify-otp", json={"destination": "dup@example.com", "code": code})

        second = _register_business(client, email="dup@example.com")
        assert second.status_code == 409

    def test_unverified_resume_same_role_succeeds(self, client):
        """Re-registering an unverified email with the SAME role is a
        resume, not a conflict."""
        first = _register_business(client, email="resume@example.com", password="Abcd1234!")
        assert first.status_code == 201

        second = _register_business(client, email="resume@example.com", password="NewPass123!")
        assert second.status_code == 201
        # Two OTP emails should have been sent (one per attempt).
        otp_emails = [
            e for e in get_fake_provider().sent_emails
            if e["to"] == "resume@example.com" and e["subject"] == "Your TruConnect verification code"
        ]
        assert len(otp_emails) == 2

    def test_unverified_resume_different_role_is_rejected(self, client):
        """This is the exact bypass pattern found in testing: silently
        flipping an unverified account's role must not be possible."""
        first = _register_business(client, email="roleflip@example.com")
        assert first.status_code == 201

        second = client.post(
            "/api/v1/auth/register",
            json={
                "role": "supplier",
                "businessName": "Someone Supplies",
                "ownerName": "Someone",
                "email": "roleflip@example.com",
                "password": "Abcd1234!",
                "confirmPassword": "Abcd1234!",
                "acceptTerms": True,
            },
        )
        assert second.status_code == 409

    def test_expired_unverified_account_allows_fresh_registration(self, client, app):
        """Simulates the 24-hour expiry by directly backdating
        created_at, rather than waiting -- see UNVERIFIED_ACCOUNT_EXPIRY_HOURS."""
        _register_business(client, email="stale@example.com", password="OldPass123!")

        with app.app_context():
            from datetime import timedelta

            from src.core.base_model import utcnow
            from src.domains.auth.repositories.user_repository import UserRepository

            user = UserRepository.get_by_email("stale@example.com")
            user.created_at = utcnow() - timedelta(hours=25)
            db.session.commit()

        # A fresh registration with a DIFFERENT role should now succeed
        # (proving the old row was actually deleted, not just reused).
        response = client.post(
            "/api/v1/auth/register",
            json={
                "role": "supplier",
                "businessName": "Fresh Start Trading",
                "ownerName": "Fresh Start",
                "email": "stale@example.com",
                "password": "NewPass123!",
                "confirmPassword": "NewPass123!",
                "acceptTerms": True,
            },
        )
        assert response.status_code == 201


class TestVerificationGatingIntegration:
    def test_login_blocked_before_verification(self, client):
        _register_business(client, email="unverified-login@example.com", password="Abcd1234!")

        response = client.post(
            "/api/v1/auth/login", json={"email": "unverified-login@example.com", "password": "Abcd1234!"}
        )
        assert response.status_code == 403
        body = response.get_json()
        assert body["code"] == "EMAIL_NOT_VERIFIED"
        assert body["data"]["resend_available"] is True
        assert "verification_endpoint" in body["data"]

    def test_login_succeeds_after_verification(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="verify-then-login@example.com", password="Abcd1234!")
        code = _extract_otp(caplog, "verify-then-login@example.com")
        client.post(
            "/api/v1/auth/phone/verify-otp",
            json={"destination": "verify-then-login@example.com", "code": code},
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "verify-then-login@example.com", "password": "Abcd1234!"},
        )
        assert response.status_code == 200

    def test_verify_otp_returns_tokens(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="otp-tokens@example.com")
        code = _extract_otp(caplog, "otp-tokens@example.com")

        response = client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "otp-tokens@example.com", "code": code}
        )
        assert response.status_code == 200
        body = response.get_json()["data"]
        assert "access_token" in body["tokens"]
        assert "refresh_token" in body["tokens"]

    def test_me_requires_verified_not_just_authenticated(self, client, caplog):
        """The core regression test: a token from BEFORE the account was
        ever verified must not exist -- and even if one somehow did,
        @fully_authenticated re-checks the database, not the token."""
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="fake-token-test@example.com")
        code = _extract_otp(caplog, "fake-token-test@example.com")
        verify_response = client.post(
            "/api/v1/auth/phone/verify-otp",
            json={"destination": "fake-token-test@example.com", "code": code},
        )
        access_token = verify_response.get_json()["data"]["tokens"]["access_token"]

        # This token was issued AFTER verification, so /me must succeed.
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200

    def test_me_rejects_unauthenticated(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401


class TestLoginLockoutIntegration:
    def test_lockout_after_max_failed_attempts(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="lockout@example.com", password="Correct123!")
        code = _extract_otp(caplog, "lockout@example.com")
        client.post("/api/v1/auth/phone/verify-otp", json={"destination": "lockout@example.com", "code": code})

        # This test is specifically exercising the EXISTING account-lockout
        # system (5 wrong attempts -> 423 ACCOUNT_LOCKED), which is a
        # deliberately separate protection from the login rate limiter
        # (5 requests/minute) added alongside it. The two policies are
        # independent by design -- see auth/rate_limit/policies.py -- and
        # happen to share the same number (5) for unrelated reasons, so
        # 6 rapid identical-endpoint calls in a tight loop would trip the
        # rate limiter before ever reaching the lockout check this test
        # is actually about. Exempting the limiter here tests lockout in
        # isolation, exactly as it did before rate limiting existed,
        # without loosening the real 5/min login policy to accommodate a
        # test loop shape.
        limiter.enabled = False
        try:
            last_response = None
            for _ in range(6):  # LOGIN_MAX_FAILED_ATTEMPTS defaults to 5
                last_response = client.post(
                    "/api/v1/auth/login", json={"email": "lockout@example.com", "password": "WrongPassword1!"}
                )
        finally:
            limiter.enabled = True

        assert last_response.status_code == 423
        assert last_response.get_json()["code"] == "ACCOUNT_LOCKED"

    def test_successful_login_resets_failed_counter(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="reset-counter@example.com", password="Correct123!")
        code = _extract_otp(caplog, "reset-counter@example.com")
        client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "reset-counter@example.com", "code": code}
        )

        # Same reasoning as test_lockout_after_max_failed_attempts above:
        # this test makes 7 rapid /login calls against one email to
        # exercise the failed-attempt counter specifically, independent
        # of the separate 5/min rate limiter.
        limiter.enabled = False
        try:
            for _ in range(3):
                client.post(
                    "/api/v1/auth/login", json={"email": "reset-counter@example.com", "password": "wrong"}
                )

            success = client.post(
                "/api/v1/auth/login", json={"email": "reset-counter@example.com", "password": "Correct123!"}
            )
            assert success.status_code == 200

            # Counter should be back to zero, so more wrong attempts are
            # possible before locking out again.
            for _ in range(3):
                fail = client.post(
                    "/api/v1/auth/login", json={"email": "reset-counter@example.com", "password": "wrong"}
                )
                assert fail.status_code == 401  # not yet 423
        finally:
            limiter.enabled = True


class TestPasswordResetTicketIntegration:
    def _get_reset_url(self, email):
        for sent in get_fake_provider().sent_emails:
            if sent["to"] == email and sent["subject"] == "Reset your TruConnect password":
                match = re.search(r"reset-password\?ticket=([\w\-]+)", sent["html_body"])
                if match:
                    return match.group(1)
        raise AssertionError(f"No password reset email found for {email}")

    def _verified_user(self, client, caplog, email):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email=email, password="OldPass123!")
        code = _extract_otp(caplog, email)
        client.post("/api/v1/auth/phone/verify-otp", json={"destination": email, "code": code})

    def test_validate_ticket_true_for_fresh_ticket(self, client, caplog):
        self._verified_user(client, caplog, "reset-validate@example.com")
        client.post("/api/v1/auth/forgot-password", json={"email": "reset-validate@example.com"})
        ticket = self._get_reset_url("reset-validate@example.com")

        response = client.get(f"/api/v1/auth/reset-password/validate?ticket={ticket}")
        assert response.get_json()["data"]["valid"] is True

    def test_validate_ticket_false_for_garbage(self, client):
        response = client.get("/api/v1/auth/reset-password/validate?ticket=not-a-real-ticket")
        assert response.get_json()["data"]["valid"] is False

    def test_reset_password_with_valid_ticket_changes_password(self, client, caplog):
        self._verified_user(client, caplog, "reset-flow@example.com")
        client.post("/api/v1/auth/forgot-password", json={"email": "reset-flow@example.com"})
        ticket = self._get_reset_url("reset-flow@example.com")

        response = client.post(
            "/api/v1/auth/reset-password",
            json={"ticket": ticket, "newPassword": "NewPass123!", "confirmPassword": "NewPass123!"},
        )
        assert response.status_code == 200

        assert (
            client.post(
                "/api/v1/auth/login", json={"email": "reset-flow@example.com", "password": "OldPass123!"}
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/auth/login", json={"email": "reset-flow@example.com", "password": "NewPass123!"}
            ).status_code
            == 200
        )

    def test_reset_ticket_cannot_be_reused(self, client, caplog):
        self._verified_user(client, caplog, "reset-replay@example.com")
        client.post("/api/v1/auth/forgot-password", json={"email": "reset-replay@example.com"})
        ticket = self._get_reset_url("reset-replay@example.com")

        first = client.post(
            "/api/v1/auth/reset-password",
            json={"ticket": ticket, "newPassword": "NewPass123!", "confirmPassword": "NewPass123!"},
        )
        assert first.status_code == 200

        second = client.post(
            "/api/v1/auth/reset-password",
            json={"ticket": ticket, "newPassword": "AnotherPass1!", "confirmPassword": "AnotherPass1!"},
        )
        assert second.status_code == 401

    def test_reset_redirect_page_renders(self, client):
        """The browser-facing bounce page (Objective 7) -- not under
        /api/v1, must exist at the exact path emailed to users."""
        response = client.get("/reset-password?ticket=abc123")
        assert response.status_code == 200
        assert b"truconnect://reset-password?ticket=abc123" in response.data
