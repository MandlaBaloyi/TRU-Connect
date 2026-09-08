"""
Web Portal Authentication Routes (V2 2.10).

A SECOND BLUEPRINT RATHER THAN FLAGS ON THE FIRST. routes.py is the
mobile contract and is deliberately untouched by this work: the app is
shipped, its login returns tokens in a JSON body, and every branch added
to that handler would be a branch a mobile release could trip over. The
two clients genuinely differ -- different transport, different lifetime,
different set of roles allowed through -- so they get different routes
instead of one route full of `if client == "web"`.

WHAT IS SHARED IS EVERYTHING THAT MATTERS: the same AuthService, the
same verification gate, the same audit stream, and BOTH throttles --
the account lockout, which was always keyed on the email alone, and the
per-minute rate limit, which had to be given an explicit shared scope to
behave the same way (see LOGIN_SCOPE in rate_limit/policies.py). Five
failed attempts here and there are five, not ten.

WHY NO TOKEN EVER APPEARS IN THESE RESPONSE BODIES. Putting it in the
JSON "just in case the client wants it" would hand the browser exactly
the copy the httpOnly cookie exists to deny it. The body carries the
user; the credential travels only in Set-Cookie.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated
from src.core.responses import error_response, success_response
from src.domains.auth.rate_limit import policies as rate_limit_policies
from src.domains.auth.schemas.auth_schemas import LoginSchema
from src.domains.auth.services.auth_service import AuthService
from src.domains.auth.services.web_session_service import WebSessionService
from src.domains.security.rate_limit.limiter import limiter

auth_web_bp = Blueprint("auth_web", __name__)

_login_schema = LoginSchema()


def _flatten_errors(messages) -> list:
    flat: list = []
    if isinstance(messages, dict):
        for field, field_errors in messages.items():
            if isinstance(field_errors, list):
                flat.extend(f"{field}: {msg}" for msg in field_errors)
            else:
                flat.append(f"{field}: {field_errors}")
    elif isinstance(messages, list):
        flat.extend(str(m) for m in messages)
    return flat


@auth_web_bp.post("/login")
# THE SAME BUCKET AS THE MOBILE LOGIN -- five attempts a minute against
# an email, not five per surface. shared_limit rather than
# limit(scope=...) for the reason spelled out on the mobile route: only
# shared_limit removes the endpoint from the key.
@limiter.shared_limit(
    rate_limit_policies.LOGIN,
    rate_limit_policies.LOGIN_SCOPE,
    key_func=rate_limit_policies.login_key_func,
)
def web_login():
    """Signs a supplier into the browser portal.

    Rejects `business` with WRONG_PORTAL -- see WrongPortalError on why
    that is not folded into the generic 403.
    """
    payload = request.get_json(silent=True) or {}
    try:
        data = _login_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    user, tokens = WebSessionService.login(
        data["email"], data["password"], ip_address=request.remote_addr
    )

    # success_response returns (body, status); the cookies have to go on
    # a real Response object, so it is materialised here rather than
    # returned as a tuple.
    response = jsonify(
        {"success": True, "message": "Signed in.", "data": {"user": user.to_public_dict()}}
    )
    return WebSessionService.attach(response, tokens), 200


@auth_web_bp.post("/refresh")
@limiter.limit(rate_limit_policies.REFRESH)
@jwt_required(refresh=True)
def web_refresh():
    """Rotates the session. The browser sends nothing: the refresh
    cookie is attached automatically because this path is under
    JWT_REFRESH_COOKIE_PATH, and the X-CSRF-TOKEN header is what proves
    the request came from our own page.

    NOT OPTIONAL AUTH, unlike logout below. A failed refresh SHOULD be a
    401 -- that is the signal the client uses to send someone back to
    sign-in.
    """
    claims = get_jwt()
    tokens = WebSessionService.refresh(
        current_jti=claims.get("jti"),
        user_id=get_jwt_identity(),
        ip_address=request.remote_addr,
    )
    response = jsonify({"success": True, "message": "Session refreshed.", "data": None})
    return WebSessionService.attach(response, tokens), 200


@auth_web_bp.post("/logout")
@jwt_required(refresh=True, optional=True)
def web_logout():
    """Ends the session.

    OPTIONAL AUTH, AND THAT IS THE DESIGN. Signing out must always
    succeed. If this required a valid refresh token, then the one case
    where a user most wants the button to work -- an expired or already
    revoked session sitting in a stale tab -- is the exact case where it
    would return 401 and leave the cookies in place. So: revoke the row
    if there is a live token to revoke, and clear the cookies either
    way.

    A logout that cannot fail is also a logout nobody has to be talked
    through over the phone.
    """
    identity = get_jwt_identity()
    if identity is not None:
        claims = get_jwt()
        AuthService.logout(user_id=identity, refresh_token_jti=claims.get("jti"))

    response = jsonify({"success": True, "message": "Signed out.", "data": None})
    return WebSessionService.clear(response), 200


@auth_web_bp.get("/session")
@fully_authenticated
def web_session():
    """Who am I, according to the cookie.

    THE PORTAL'S FIRST CALL ON EVERY PAGE LOAD, because the browser
    cannot read the httpOnly cookie to find out for itself -- it can
    only ask. A 401 here is how the client learns it is signed out.

    @fully_authenticated re-checks the database rather than trusting the
    token's claims, which is what makes a supplier deactivated an hour
    ago actually lose the tab they still have open.
    """
    user = AuthService.get_current_user(get_jwt_identity())
    return success_response(data={"user": user.to_public_dict()})
