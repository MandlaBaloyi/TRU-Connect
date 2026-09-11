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

    def test_rejects_missing_privacy_policy(self):
        with pytest.raises(Exception):
            BusinessRegisterSchema().load(self._valid_payload(acceptPrivacyPolicy=False))


class TestSupplierRegisterSchema:
    def test_accepts_valid_payload(self):
        data = SupplierRegisterSchema().load(
            {
                "ownerName": "Naledi Dlamini",
                "email": "naledi@example.com",
                "password": "Abcd1234!",
                "confirmPassword": "Abcd1234!",
                "acceptTerms": True,
            }
        )
        assert data["owner_name"] == "Naledi Dlamini"


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


def _register_business(client, email="thabo@example.com", password="Abcd1234!"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "role": "business",
            "firstName": "Thabo",
            "lastName": "Nkosi",
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

        last_response = None
        for _ in range(6):  # LOGIN_MAX_FAILED_ATTEMPTS defaults to 5
            last_response = client.post(
                "/api/v1/auth/login", json={"email": "lockout@example.com", "password": "WrongPassword1!"}
            )
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


class TestSecurityHardeningIntegration:
    """
    Ref: security review -- OWASP-adjacent checks against the existing
    Auth surface, before Loan Book adds new resources that need their
    own authorization/isolation tests (see tests/domains/auth/ for the
    broader sweep -- this class covers what's testable TODAY, against
    the /me endpoint specifically).

    STATUS CODE CONVENTION CONFIRMED BY RUNNING THESE AGAINST THE REAL
    APP: Flask-JWT-Extended returns 401 for NO token at all, but 422
    Unprocessable Entity for a token that IS present but invalid --
    malformed, bad signature, wrong key, tampered claims. This is FJE's
    real, deliberate behaviour, not a bug -- these tests assert 422 for
    "present but broken", 401 only for "nothing to even parse".
    """

    def test_tampered_jwt_signature_is_rejected(self, client, caplog):
        """A token with its signature altered (everything else intact)
        must never be accepted."""
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="jwt-tamper@example.com")
        code = _extract_otp(caplog, "jwt-tamper@example.com")
        verify_response = client.post(
            "/api/v1/auth/phone/verify-otp",
            json={"destination": "jwt-tamper@example.com", "code": code},
        )
        real_token = verify_response.get_json()["data"]["tokens"]["access_token"]

        header, payload, signature = real_token.rsplit(".", 2)
        tampered_char = "A" if signature[-1] != "A" else "B"
        tampered_token = f"{header}.{payload}.{signature[:-1]}{tampered_char}"

        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"}
        )
        assert response.status_code == 422

    def test_jwt_signed_with_a_different_key_is_rejected(self, client, caplog):
        """A well-formed token signed with a DIFFERENT secret entirely --
        simulating an attacker with their own JWT library, guessing at
        the payload shape."""
        import logging

        import jwt as pyjwt

        caplog.set_level(logging.INFO)
        _register_business(client, email="jwt-wrongkey@example.com")
        code = _extract_otp(caplog, "jwt-wrongkey@example.com")
        verify_response = client.post(
            "/api/v1/auth/phone/verify-otp",
            json={"destination": "jwt-wrongkey@example.com", "code": code},
        )
        real_token = verify_response.get_json()["data"]["tokens"]["access_token"]
        real_payload = pyjwt.decode(real_token, options={"verify_signature": False})

        forged_token = pyjwt.encode(real_payload, "an-attackers-guessed-key", algorithm="HS256")

        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {forged_token}"}
        )
        assert response.status_code == 422

    def test_me_never_leaks_another_users_data(self, client, caplog):
        """Two real, separately-registered users. Confirms /me for user
        A's token can never return user B's data -- the endpoint trusts
        ONLY the token's own identity, never anything else derivable
        from the request."""
        import logging

        caplog.set_level(logging.INFO)

        _register_business(client, email="user-a@example.com", password="PasswordA1!")
        code_a = _extract_otp(caplog, "user-a@example.com")
        token_a = client.post(
            "/api/v1/auth/phone/verify-otp",
            json={"destination": "user-a@example.com", "code": code_a},
        ).get_json()["data"]["tokens"]["access_token"]

        _register_business(client, email="user-b@example.com", password="PasswordB1!")
        code_b = _extract_otp(caplog, "user-b@example.com")
        token_b = client.post(
            "/api/v1/auth/phone/verify-otp",
            json={"destination": "user-b@example.com", "code": code_b},
        ).get_json()["data"]["tokens"]["access_token"]

        response_a = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        response_b = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})

        assert response_a.get_json()["data"]["email"] == "user-a@example.com"
        assert response_b.get_json()["data"]["email"] == "user-b@example.com"
        assert response_a.get_json()["data"]["email"] != response_b.get_json()["data"]["email"]

    def test_malformed_authorization_header_is_rejected_not_500(self, client):
        """A handful of malformed-but-plausible headers -- none of these
        should ever produce a 500. The real security property under
        test is purely 'never a 500' -- a malformed-but-present token is
        422, a missing/empty/unparseable header is 401."""
        malformed_headers = [
            "Bearer",
            "Bearer ",
            "NotBearer sometoken",
            "Bearer not.a.jwt",
            "",
        ]
        for header_value in malformed_headers:
            response = client.get("/api/v1/auth/me", headers={"Authorization": header_value})
            assert response.status_code in (400, 401, 422), (
                f"header {header_value!r} produced {response.status_code}, expected 400/401/422"
            )
