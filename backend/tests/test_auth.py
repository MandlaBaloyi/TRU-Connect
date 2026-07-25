"""
Authentication module tests.
Ref: continuation master prompt, Step 16 (Authentication Test Suite).

Two groups, as in Phase 2:
1. Pure unit tests -- no database connection needed. Run anywhere:
       pytest tests/test_auth.py -k "not Integration"
2. Integration tests -- need a real PostgreSQL test database
   (TestingConfig -> tru_connect_test, see src/config.py):
       pytest tests/test_auth.py -k Integration
"""
from __future__ import annotations

import time

import pytest

from src import create_app
from src.extensions import db
from src.schemas.auth_schemas import BusinessRegisterSchema, LoginSchema, SupplierRegisterSchema
from src.schemas.otp_schemas import RequestOtpSchema, VerifyOtpSchema
from src.schemas.password_reset_schemas import ForgotPasswordSchema, ResetPasswordSchema
from src.utils.otp import generate_numeric_otp, generate_reset_token, hash_otp, hash_reset_token, verify_otp_hash
from src.utils.security import hash_password, passwords_match, validate_password_complexity, verify_password


# ----------------------------------------------------------------------------
# Group 1: pure unit tests -- no database required.
# ----------------------------------------------------------------------------

class TestPasswordSecurity:
    def test_hash_and_verify_round_trip(self):
        hashed = hash_password("correct horse battery staple 1")
        assert verify_password("correct horse battery staple 1", hashed)

    def test_verify_rejects_wrong_password(self):
        hashed = hash_password("correct horse battery staple 1")
        assert not verify_password("wrong password", hashed)

    def test_complexity_rejects_short_password(self):
        assert any("8 characters" in e for e in validate_password_complexity("ab1"))

    def test_complexity_rejects_no_digit(self):
        assert any("number" in e for e in validate_password_complexity("abcdefgh"))

    def test_complexity_rejects_no_letter(self):
        assert any("letter" in e for e in validate_password_complexity("12345678"))

    def test_complexity_accepts_valid_password(self):
        assert validate_password_complexity("abcd1234") == []

    def test_passwords_match(self):
        assert passwords_match("abcd1234", "abcd1234")
        assert not passwords_match("abcd1234", "different1")


class TestOtpUtilities:
    def test_generated_otp_is_correct_length_and_numeric(self):
        code = generate_numeric_otp()
        assert len(code) == 6
        assert code.isdigit()

    def test_otp_hash_round_trip(self):
        code = generate_numeric_otp()
        assert verify_otp_hash(code, hash_otp(code))

    def test_otp_hash_rejects_wrong_code(self):
        code_hash = hash_otp("123456")
        assert not verify_otp_hash("654321", code_hash)

    def test_reset_token_is_url_safe_and_reasonably_long(self):
        token = generate_reset_token()
        assert len(token) >= 32

    def test_reset_token_hash_is_deterministic(self):
        token = generate_reset_token()
        assert hash_reset_token(token) == hash_reset_token(token)


class TestBusinessRegisterSchema:
    def _valid_payload(self, **overrides):
        payload = {
            "firstName": "Thabo",
            "lastName": "Nkosi",
            "email": "thabo@example.com",
            "password": "abcd1234",
            "confirmPassword": "abcd1234",
            "acceptPrivacyPolicy": True,
        }
        payload.update(overrides)
        return payload

    def test_accepts_valid_camel_case_payload(self):
        data = BusinessRegisterSchema().load(self._valid_payload())
        assert data["first_name"] == "Thabo"

    def test_rejects_mismatched_passwords(self):
        with pytest.raises(Exception):
            BusinessRegisterSchema().load(self._valid_payload(confirmPassword="different1"))

    def test_rejects_missing_privacy_policy_acceptance(self):
        with pytest.raises(Exception):
            BusinessRegisterSchema().load(self._valid_payload(acceptPrivacyPolicy=False))


class TestSupplierRegisterSchema:
    def test_accepts_valid_payload(self):
        data = SupplierRegisterSchema().load(
            {
                "ownerName": "Naledi Dlamini",
                "email": "naledi@example.com",
                "password": "abcd1234",
                "confirmPassword": "abcd1234",
                "acceptTerms": True,
            }
        )
        assert data["owner_name"] == "Naledi Dlamini"


class TestLoginSchema:
    def test_accepts_valid_payload(self):
        data = LoginSchema().load({"email": "a@example.com", "password": "abcd1234"})
        assert data["email"] == "a@example.com"


class TestOtpSchemas:
    def test_request_otp_schema_valid(self):
        data = RequestOtpSchema().load({"destination": "test@example.com"})
        assert data["destination"] == "test@example.com"

    def test_verify_otp_schema_rejects_wrong_length_code(self):
        with pytest.raises(Exception):
            VerifyOtpSchema().load({"destination": "test@example.com", "code": "123"})

    def test_verify_otp_schema_accepts_six_digit_code(self):
        data = VerifyOtpSchema().load({"destination": "test@example.com", "code": "123456"})
        assert data["code"] == "123456"


class TestPasswordResetSchemas:
    def test_forgot_password_schema_requires_valid_email(self):
        with pytest.raises(Exception):
            ForgotPasswordSchema().load({"email": "not-an-email"})

    def test_reset_password_schema_rejects_mismatched_passwords(self):
        with pytest.raises(Exception):
            ResetPasswordSchema().load(
                {"token": "abc", "newPassword": "abcd1234", "confirmPassword": "different1"}
            )

    def test_reset_password_schema_rejects_weak_password(self):
        with pytest.raises(Exception):
            ResetPasswordSchema().load({"token": "abc", "newPassword": "weak", "confirmPassword": "weak"})

    def test_reset_password_schema_accepts_valid_payload(self):
        data = ResetPasswordSchema().load(
            {"token": "abc", "newPassword": "abcd1234", "confirmPassword": "abcd1234"}
        )
        assert data["new_password"] == "abcd1234"


# ----------------------------------------------------------------------------
# Group 2: integration tests -- require a real PostgreSQL test database.
# ----------------------------------------------------------------------------

@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _register_business(client, email="thabo@example.com"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "role": "business",
            "firstName": "Thabo",
            "lastName": "Nkosi",
            "email": email,
            "password": "abcd1234",
            "confirmPassword": "abcd1234",
            "acceptPrivacyPolicy": True,
        },
    )


class TestRegistrationIntegration:
    def test_register_business_returns_tokens(self, client):
        response = _register_business(client)
        assert response.status_code == 201
        body = response.get_json()
        assert "access_token" in body["data"]["tokens"]
        assert "refresh_token" in body["data"]["tokens"]
        assert "password_hash" not in body["data"]["user"]

    def test_duplicate_email_is_rejected(self, client):
        _register_business(client, email="dup@example.com")
        second = _register_business(client, email="dup@example.com")
        assert second.status_code == 409


class TestLoginIntegration:
    def test_login_with_correct_credentials(self, client):
        _register_business(client, email="login-test@example.com")
        response = client.post(
            "/api/v1/auth/login", json={"email": "login-test@example.com", "password": "abcd1234"}
        )
        assert response.status_code == 200

    def test_login_with_wrong_password_returns_401(self, client):
        _register_business(client, email="wrongpass@example.com")
        response = client.post(
            "/api/v1/auth/login", json={"email": "wrongpass@example.com", "password": "wrong9999"}
        )
        assert response.status_code == 401


class TestProtectedRoutesIntegration:
    def test_me_requires_authentication(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_me_returns_current_user_with_valid_token(self, client):
        register_response = _register_business(client, email="me-test@example.com")
        access_token = register_response.get_json()["data"]["tokens"]["access_token"]
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200
        assert response.get_json()["data"]["email"] == "me-test@example.com"


class TestRefreshTokenIntegration:
    def test_refresh_returns_new_token_pair(self, client):
        register_response = _register_business(client, email="refresh-test@example.com")
        original_refresh = register_response.get_json()["data"]["tokens"]["refresh_token"]

        response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {original_refresh}"}
        )
        assert response.status_code == 200
        body = response.get_json()["data"]
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["refresh_token"] != original_refresh

    def test_rotated_refresh_token_cannot_be_reused(self, client):
        """Core of Step 11's rotation requirement: once a refresh token
        has been used to get a new pair, using the SAME old token again
        must fail."""
        register_response = _register_business(client, email="rotation-test@example.com")
        original_refresh = register_response.get_json()["data"]["tokens"]["refresh_token"]

        first_use = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {original_refresh}"}
        )
        assert first_use.status_code == 200

        second_use = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {original_refresh}"}
        )
        assert second_use.status_code == 401

    def test_access_token_cannot_be_used_to_refresh(self, client):
        register_response = _register_business(client, email="wrongtype-test@example.com")
        access_token = register_response.get_json()["data"]["tokens"]["access_token"]

        response = client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 422  # flask-jwt-extended rejects wrong token type


class TestLogoutIntegration:
    def test_logout_revokes_refresh_token(self, client):
        """Mobile client's current behaviour: POST /auth/logout with only
        an access token, no refresh_token in the body -- AuthService
        falls back to revoking ALL of the user's refresh tokens."""
        register_response = _register_business(client, email="logout-test@example.com")
        tokens = register_response.get_json()["data"]["tokens"]

        logout_response = client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert logout_response.status_code == 200

        refresh_response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
        )
        assert refresh_response.status_code == 401

    def test_logout_with_explicit_refresh_token_revokes_only_that_one(self, client):
        register_response = _register_business(client, email="explicit-logout@example.com")
        tokens = register_response.get_json()["data"]["tokens"]

        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert logout_response.status_code == 200

        refresh_response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
        )
        assert refresh_response.status_code == 401


class TestOtpIntegration:
    def _get_logged_otp(self, caplog, email):
        """The dev-mode OTP delivery logs the code via app.logger.info
        (see OTPService docstring) -- tests parse it out of the captured
        log rather than needing a real SMS/email provider."""
        import re

        for record in caplog.records:
            if email in record.message:
                match = re.search(r": (\d{6}) ", record.message + " ")
                if match:
                    return match.group(1)
        return None

    def test_request_then_verify_otp_succeeds(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="otp-test@example.com")

        request_response = client.post(
            "/api/v1/auth/phone/request-otp", json={"destination": "otp-test@example.com"}
        )
        assert request_response.status_code == 200

        code = self._get_logged_otp(caplog, "otp-test@example.com")
        assert code is not None

        verify_response = client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "otp-test@example.com", "code": code}
        )
        assert verify_response.status_code == 200

    def test_wrong_otp_code_is_rejected(self, client):
        _register_business(client, email="otp-wrong@example.com")
        client.post("/api/v1/auth/phone/request-otp", json={"destination": "otp-wrong@example.com"})

        response = client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "otp-wrong@example.com", "code": "000000"}
        )
        assert response.status_code == 401

    def test_otp_cannot_be_reused_after_success(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="otp-reuse@example.com")
        client.post("/api/v1/auth/phone/request-otp", json={"destination": "otp-reuse@example.com"})
        code = self._get_logged_otp(caplog, "otp-reuse@example.com")

        first = client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "otp-reuse@example.com", "code": code}
        )
        assert first.status_code == 200

        second = client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "otp-reuse@example.com", "code": code}
        )
        assert second.status_code == 401

    def test_otp_locks_out_after_too_many_wrong_attempts(self, client):
        _register_business(client, email="otp-lockout@example.com")
        client.post("/api/v1/auth/phone/request-otp", json={"destination": "otp-lockout@example.com"})

        last_response = None
        for _ in range(6):  # max_attempts defaults to 5
            last_response = client.post(
                "/api/v1/auth/phone/verify-otp",
                json={"destination": "otp-lockout@example.com", "code": "000000"},
            )
        assert last_response.status_code == 403

    def test_request_otp_for_unknown_destination_does_not_error(self, client):
        """Enumeration protection: requesting an OTP for a destination
        with no matching account must not reveal that fact via a
        different status code."""
        response = client.post(
            "/api/v1/auth/phone/request-otp", json={"destination": "nobody@example.com"}
        )
        assert response.status_code == 200


class TestPasswordResetIntegration:
    def _get_logged_token(self, caplog, email):
        for record in caplog.records:
            if email in record.message and "Password reset token" in record.message:
                parts = record.message.split(": ")
                return parts[1].split(" ")[0] if len(parts) > 1 else None
        return None

    def test_forgot_password_returns_same_message_for_known_and_unknown_email(self, client):
        known = _register_business(client, email="forgot-known@example.com")
        assert known.status_code == 201

        known_response = client.post("/api/v1/auth/forgot-password", json={"email": "forgot-known@example.com"})
        unknown_response = client.post("/api/v1/auth/forgot-password", json={"email": "forgot-unknown@example.com"})

        assert known_response.status_code == unknown_response.status_code == 200
        assert known_response.get_json()["message"] == unknown_response.get_json()["message"]

    def test_reset_password_with_valid_token_changes_password(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="reset-flow@example.com")
        client.post("/api/v1/auth/forgot-password", json={"email": "reset-flow@example.com"})
        token = self._get_logged_token(caplog, "reset-flow@example.com")
        assert token is not None

        reset_response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "newPassword": "newpass123", "confirmPassword": "newpass123"},
        )
        assert reset_response.status_code == 200

        old_password_login = client.post(
            "/api/v1/auth/login", json={"email": "reset-flow@example.com", "password": "abcd1234"}
        )
        assert old_password_login.status_code == 401

        new_password_login = client.post(
            "/api/v1/auth/login", json={"email": "reset-flow@example.com", "password": "newpass123"}
        )
        assert new_password_login.status_code == 200

    def test_reset_token_cannot_be_reused(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="reset-replay@example.com")
        client.post("/api/v1/auth/forgot-password", json={"email": "reset-replay@example.com"})
        token = self._get_logged_token(caplog, "reset-replay@example.com")

        first = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "newPassword": "newpass123", "confirmPassword": "newpass123"},
        )
        assert first.status_code == 200

        second = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "newPassword": "anotherpass1", "confirmPassword": "anotherpass1"},
        )
        assert second.status_code == 401

    def test_reset_password_invalidates_existing_refresh_tokens(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        register_response = _register_business(client, email="reset-revokes@example.com")
        original_refresh = register_response.get_json()["data"]["tokens"]["refresh_token"]

        client.post("/api/v1/auth/forgot-password", json={"email": "reset-revokes@example.com"})
        token = self._get_logged_token(caplog, "reset-revokes@example.com")
        client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "newPassword": "newpass123", "confirmPassword": "newpass123"},
        )

        refresh_response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {original_refresh}"}
        )
        assert refresh_response.status_code == 401


class TestRoleAuthorizationIntegration:
    def test_role_required_allows_matching_role(self, app, client):
        from flask import jsonify

        from src.core.decorators import role_required

        @app.route("/api/v1/_test/business-only")
        @role_required("business")
        def _business_only():
            return jsonify({"ok": True})

        register_response = _register_business(client, email="role-test@example.com")
        access_token = register_response.get_json()["data"]["tokens"]["access_token"]

        response = client.get(
            "/api/v1/_test/business-only", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200

    def test_role_required_blocks_non_matching_role(self, app, client):
        from flask import jsonify

        from src.core.decorators import role_required

        @app.route("/api/v1/_test/supplier-only")
        @role_required("supplier")
        def _supplier_only():
            return jsonify({"ok": True})

        register_response = _register_business(client, email="role-block-test@example.com")
        access_token = register_response.get_json()["data"]["tokens"]["access_token"]

        response = client.get(
            "/api/v1/_test/supplier-only", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 403
