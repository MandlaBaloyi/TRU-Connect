"""
Authentication Routes.
Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1; continuation
master prompt, Steps 7-14.

Routes ONLY: validate the request (via Marshmallow), call the service
layer, return the standard response envelope. No business logic and no
direct SQLAlchemy access here.
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jti, get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.responses import error_response, success_response
from src.schemas.auth_schemas import BusinessRegisterSchema, LoginSchema, SupplierRegisterSchema
from src.schemas.otp_schemas import RequestOtpSchema, VerifyOtpSchema
from src.schemas.password_reset_schemas import ForgotPasswordSchema, ResetPasswordSchema
from src.services.auth_service import AuthService
from src.services.otp_service import OTPService
from src.services.password_reset_service import PasswordResetService

auth_bp = Blueprint("auth", __name__)

_business_register_schema = BusinessRegisterSchema()
_supplier_register_schema = SupplierRegisterSchema()
_login_schema = LoginSchema()
_request_otp_schema = RequestOtpSchema()
_verify_otp_schema = VerifyOtpSchema()
_forgot_password_schema = ForgotPasswordSchema()
_reset_password_schema = ResetPasswordSchema()


def _flatten_errors(messages) -> list:
    flat: list = []
    if isinstance(messages, dict):
        for field, field_errors in messages.items():
            if isinstance(field_errors, list):
                for msg in field_errors:
                    flat.append(f"{field}: {msg}")
            else:
                flat.append(f"{field}: {field_errors}")
    elif isinstance(messages, list):
        flat.extend(str(m) for m in messages)
    return flat


# ------------------------------------------------------------------------
# Steps 7-8 -- Registration & Login (UNCHANGED from Phase 2)
# ------------------------------------------------------------------------

@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    role = payload.get("role")

    if role == "business":
        schema = _business_register_schema
    elif role == "supplier":
        schema = _supplier_register_schema
    else:
        return error_response(
            message="Validation failed", errors=["role: must be 'business' or 'supplier'"], status_code=422
        )

    try:
        data = schema.load({k: v for k, v in payload.items() if k != "role"})
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    if role == "business":
        user, tokens = AuthService.register_business(data)
        message = "Business account created successfully."
    else:
        user, tokens = AuthService.register_supplier(data)
        message = "Supplier account created successfully."

    return success_response(
        data={"user": user.to_public_dict(), "tokens": tokens}, message=message, status_code=201
    )


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    try:
        data = _login_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    user, tokens = AuthService.login(data["email"], data["password"])
    return success_response(data={"user": user.to_public_dict(), "tokens": tokens}, message="Login successful.")


# ------------------------------------------------------------------------
# Step 11 -- Refresh Token rotation
# ------------------------------------------------------------------------

@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """Rotation: returns a NEW access_token AND a NEW refresh_token; the
    refresh token that authenticated this request is revoked as part of
    AuthService.refresh(). The mobile app does not yet call this
    endpoint (frontend/mobile's apiClient.ts has a comment noting 401
    refresh-exchange handling is not wired up yet) -- when it is, it
    must store BOTH returned tokens, not just the access token, since
    the old refresh token stops working after this call."""
    identity = get_jwt_identity()
    claims = get_jwt()
    tokens = AuthService.refresh(current_jti=claims.get("jti"), user_id=identity)
    return success_response(data=tokens, message="Token refreshed.")


# ------------------------------------------------------------------------
# Step 10 -- Current user
# ------------------------------------------------------------------------

@auth_bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()
    user = AuthService.get_current_user(identity)
    return success_response(data=user.to_public_dict())


# ------------------------------------------------------------------------
# Step 12 -- Logout
# ------------------------------------------------------------------------

@auth_bp.post("/logout")
@jwt_required(verify_type=False)
def logout():
    """Authenticated with the caller's ACCESS token (matching what
    frontend/mobile's authService.logout() already sends). Optionally
    accepts {"refresh_token": "..."} in the body for true single-device
    revocation -- the mobile client does not send this yet, so today
    this always falls back to AuthService.logout()'s safe default
    (revoke every active refresh token for the user). See that method's
    docstring for the full rationale."""
    identity = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    raw_refresh_token = payload.get("refresh_token")

    refresh_token_jti = None
    if raw_refresh_token:
        try:
            refresh_token_jti = get_jti(raw_refresh_token)
        except Exception:  # noqa: BLE001 - any decode failure just means "no usable jti"
            refresh_token_jti = None

    AuthService.logout(user_id=identity, refresh_token_jti=refresh_token_jti)
    return success_response(message="Logged out.")


# ------------------------------------------------------------------------
# Step 13 -- OTP Verification (see src/services/otp_service.py docstring
# for why this verifies by email, not phone, given the current mobile
# registration flow)
# ------------------------------------------------------------------------

@auth_bp.post("/phone/request-otp")
def request_otp():
    payload = request.get_json(silent=True) or {}
    try:
        data = _request_otp_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    OTPService.request_otp(destination=data["destination"])
    return success_response(message="If an account exists for this destination, a verification code has been sent.")


@auth_bp.post("/phone/verify-otp")
def verify_otp():
    payload = request.get_json(silent=True) or {}
    try:
        data = _verify_otp_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    OTPService.verify_otp(destination=data["destination"], code=data["code"])
    return success_response(message="Verification successful.")


# ------------------------------------------------------------------------
# Step 14 -- Forgot / Reset Password
# ------------------------------------------------------------------------

@auth_bp.post("/forgot-password")
def forgot_password():
    payload = request.get_json(silent=True) or {}
    try:
        data = _forgot_password_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    PasswordResetService.forgot_password(data["email"])
    return success_response(
        message="If an account exists for this email, password reset instructions have been sent."
    )


@auth_bp.post("/reset-password")
def reset_password():
    payload = request.get_json(silent=True) or {}
    try:
        data = _reset_password_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    PasswordResetService.reset_password(token=data["token"], new_password=data["new_password"])
    return success_response(message="Password has been reset successfully.")
