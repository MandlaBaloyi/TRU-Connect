"""
Authentication Routes.
Ref: docs/05_BACKEND_API_SPECIFICATION.txt §5.1; Auth Hardening master
prompt, Objectives 1, 3, 6, 7, 9.

Routes ONLY: validate the request, call the service layer, return the
standard response envelope. Structured AppError subclasses raised by
services (EmailNotVerifiedError, AccountLockedError, TicketInvalidError,
etc.) are caught by the app-wide error handler -- routes do not need
their own try/except for those.
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jti, get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated
from src.core.responses import error_response, success_response
from src.domains.auth.schemas.auth_schemas import BusinessRegisterSchema, LoginSchema, SupplierRegisterSchema
from src.domains.auth.schemas.otp_schemas import RequestOtpSchema, VerifyOtpSchema
from src.domains.auth.schemas.password_reset_schemas import (
    ForgotPasswordSchema,
    ResetPasswordSchema,
    ValidateResetTicketSchema,
)
from src.domains.auth.services.auth_service import AuthService
from src.domains.auth.services.otp_service import OTPService
from src.domains.auth.services.password_reset_service import PasswordResetService
from src.domains.security.rate_limit import policies as rate_limit_policies
from src.domains.security.rate_limit.limiter import limiter

auth_bp = Blueprint("auth", __name__)

_business_register_schema = BusinessRegisterSchema()
_supplier_register_schema = SupplierRegisterSchema()
_login_schema = LoginSchema()
_request_otp_schema = RequestOtpSchema()
_verify_otp_schema = VerifyOtpSchema()
_forgot_password_schema = ForgotPasswordSchema()
_reset_password_schema = ResetPasswordSchema()
_validate_ticket_schema = ValidateResetTicketSchema()


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


@auth_bp.post("/register")
@limiter.limit(rate_limit_policies.REGISTER)
def register():
    """Creates the account and sends the verification OTP ONLY. No
    tokens are returned -- there is no valid session for an unverified
    account (Auth Hardening master prompt, Objective 1)."""
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
        user = AuthService.register_business(data)
        message = "Business account created. Check your email for a verification code."
    else:
        user = AuthService.register_supplier(data)
        message = "Supplier account created. Check your email for a verification code."

    return success_response(data={"user": user.to_public_dict()}, message=message, status_code=201)


@auth_bp.post("/login")
@limiter.limit(rate_limit_policies.LOGIN, key_func=rate_limit_policies.login_key_func)
def login():
    payload = request.get_json(silent=True) or {}
    try:
        data = _login_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    user, tokens = AuthService.login(data["email"], data["password"], ip_address=request.remote_addr)
    return success_response(data={"user": user.to_public_dict(), "tokens": tokens}, message="Login successful.")


@auth_bp.post("/refresh")
@limiter.limit(rate_limit_policies.REFRESH)
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    tokens = AuthService.refresh(
        current_jti=claims.get("jti"), user_id=identity, ip_address=request.remote_addr
    )
    return success_response(data=tokens, message="Token refreshed.")


@auth_bp.get("/me")
@fully_authenticated
def me():
    """Hardened: requires authentication AND a database-fresh VERIFIED
    AND ACTIVE status, not just a valid token (Auth Hardening master
    prompt, Objective 3)."""
    identity = get_jwt_identity()
    user = AuthService.get_current_user(identity)
    return success_response(data=user.to_public_dict())


@auth_bp.post("/logout")
@jwt_required(verify_type=False)
def logout():
    identity = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    raw_refresh_token = payload.get("refresh_token")

    refresh_token_jti = None
    if raw_refresh_token:
        try:
            refresh_token_jti = get_jti(raw_refresh_token)
        except Exception:  # noqa: BLE001
            refresh_token_jti = None

    AuthService.logout(user_id=identity, refresh_token_jti=refresh_token_jti)
    return success_response(message="Logged out.")


@auth_bp.post("/phone/request-otp")
@limiter.limit(rate_limit_policies.OTP_REQUEST)
def request_otp():
    payload = request.get_json(silent=True) or {}
    try:
        data = _request_otp_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    OTPService.request_otp(destination=data["destination"])
    return success_response(message="If an account exists for this destination, a verification code has been sent.")


@auth_bp.post("/phone/verify-otp")
@limiter.limit(rate_limit_policies.OTP_VERIFY)
def verify_otp():
    """Returns {user, tokens} on success -- this is the first
    authenticated moment for a brand-new account (Auth Hardening master
    prompt, Objective 1)."""
    payload = request.get_json(silent=True) or {}
    try:
        data = _verify_otp_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    user, tokens = OTPService.verify_otp(destination=data["destination"], code=data["code"])
    return success_response(
        data={"user": user.to_public_dict(), "tokens": tokens}, message="Verification successful."
    )


@auth_bp.post("/forgot-password")
@limiter.limit(rate_limit_policies.FORGOT_PASSWORD)
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


@auth_bp.get("/reset-password/validate")
def validate_reset_ticket():
    """Read-only check the mobile app calls on screen load, so an
    expired/invalid link shows an immediate, clear message rather than
    only failing after the user fills in a new password (Auth Hardening
    master prompt, Objective 6)."""
    try:
        data = _validate_ticket_schema.load(request.args.to_dict())
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    is_valid = PasswordResetService.validate_ticket(data["ticket"])
    return success_response(data={"valid": is_valid})


@auth_bp.post("/reset-password")
@limiter.limit(rate_limit_policies.RESET_PASSWORD)
def reset_password():
    payload = request.get_json(silent=True) or {}
    try:
        data = _reset_password_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    PasswordResetService.reset_password(ticket=data["ticket"], new_password=data["new_password"])
    return success_response(message="Password has been reset successfully.")
