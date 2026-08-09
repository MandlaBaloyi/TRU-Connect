"""
Auth's own rate-limit policies — "how many requests, how often" per
Auth route. Lives HERE, in the auth domain, not in
security/rate_limit/: security owns the shared ENGINE (limiter.py,
responses.py), each domain owns its own POLICY. Loan Book, Order Book,
Business, and Supplier each get their own sibling rate_limit/policies.py
following this exact same shape when their limits are built (Phase
2/3+) — see the stub files in those domains' own rate_limit/ folders.

Numbers below are Phase 1 starting points, approved for Auth —
explicitly NOT "final production numbers". Tune based on real usage
once real traffic exists, same spirit as security/rate_limit/limiter.py's
storage note.
"""
from __future__ import annotations

from flask import request
from flask_limiter.util import get_remote_address

from src.shared.audit.audit_types import AuditEventName

# --- Auth limits (Phase 1) --------------------------------------------

LOGIN = "5 per minute"
REGISTER = "5 per hour"
REFRESH = "30 per minute"
FORGOT_PASSWORD = "3 per hour"
RESET_PASSWORD = "5 per hour"
OTP_REQUEST = "5 per 10 minutes"
OTP_VERIFY = "10 per 10 minutes"
# GET /me and POST /logout: no policy constant — explicitly unlimited
# in Phase 1 per the approved scope.


def login_key_func() -> str:
    """
    IP + submitted email, combined into one key — NOT pure IP alone.

    WHY: login happens before a JWT exists, so there is no authenticated
    identity to key by yet — the only "identity" available is whatever
    email the request body claims. Keying by IP alone would let a shop
    with an owner phone + employee phone + tablet on one shared network
    lock EACH OTHER out after 5 total login attempts between all of
    them, regardless of which account each person is actually logging
    into. Keying by IP+email means each person trying their OWN email
    gets their own 5-per-minute allowance, while repeated attempts
    against the SAME email from the SAME network are still capped.

    KNOWN SIMPLIFICATION, DOCUMENTED RATHER THAN HIDDEN: this does not
    cap the AGGREGATE attempts one IP can make across MANY DIFFERENT
    emails (credential stuffing trying email1, email2, email3... from
    one source gets a fresh 5/minute allowance for each new email
    tried). That gap is intentionally left for a later phase — the
    EXISTING account-lockout system (see AuthService) already caps
    repeated attempts against one email regardless of source IP, so
    rate limiting and lockout are two different, complementary layers
    today, not one mechanism trying to do both jobs. Revisit if real
    abuse patterns show this specific gap matters in practice.

    Falls back to IP alone if the body has no email (e.g. malformed
    JSON) — malformed requests still get a key, they just share the
    coarser per-IP bucket rather than being exempt from limiting
    entirely.
    """
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    return f"{get_remote_address()}:{email}" if email else get_remote_address()


# --- Endpoint -> audit event mapping ------------------------------------
# Registered into security/rate_limit/responses.py's shared registry at
# app-boot time (see src/__init__.py) — responses.py never imports this
# module directly, so it stays domain-agnostic and every future domain's
# rate_limit/policies.py can register its own mapping the same way,
# without security/ needing to know any domain's routes exist.
#
# KEYED BY "api.auth.<function name>", NOT "auth.<function name>" --
# auth_bp is registered as a NESTED blueprint inside api_bp (see
# src/api/__init__.py: api_bp.register_blueprint(auth_bp, url_prefix="/auth")),
# so Flask's real endpoint naming is "<parent blueprint>.<child
# blueprint>.<function>". This was verified by actually triggering the
# rate limiter end-to-end and printing request.endpoint at the failure
# point — it does NOT match plain Flask single-blueprint convention,
# and guessing at it silently would have meant this mapping never
# matched anything, ever, in production.
RATE_LIMIT_AUDIT_EVENTS: dict[str, AuditEventName] = {
    "api.auth.login": AuditEventName.LOGIN_RATE_LIMITED,
    "api.auth.register": AuditEventName.REGISTER_RATE_LIMITED,
    "api.auth.refresh": AuditEventName.REFRESH_RATE_LIMITED,
    "api.auth.forgot_password": AuditEventName.PASSWORD_RESET_REQUEST_RATE_LIMITED,
    "api.auth.reset_password": AuditEventName.PASSWORD_RESET_RATE_LIMITED,
    "api.auth.request_otp": AuditEventName.OTP_REQUEST_RATE_LIMITED,
    "api.auth.verify_otp": AuditEventName.OTP_VERIFY_RATE_LIMITED,
}
