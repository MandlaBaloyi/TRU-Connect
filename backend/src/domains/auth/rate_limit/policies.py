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

from src.shared.audit.event_types.auth import AuthAuditEvent

# --- Auth limits (Phase 1) --------------------------------------------

LOGIN = "5 per minute"

# THE LOGIN BUCKET IS SHARED ACROSS SURFACES, and this constant is what
# makes it so.
#
# Flask-Limiter buckets per ENDPOINT by default. Once the web portal
# added a second login route, one email could be tried 5 times a minute
# at /auth/login AND 5 more at /auth/web/login -- ten attempts a minute
# against an account, from a limiter configured for five, with nothing
# in either policy looking wrong.
#
# Applied with limiter.shared_limit(LOGIN, LOGIN_SCOPE, ...) on BOTH
# routes. It has to be shared_limit specifically -- passing this as
# limit(scope=...) still prefixes the endpoint onto the key
# ("api.auth.login:auth_login"), so the two routes keep separate
# counters while looking, in review, exactly like they share one. That
# was written and believed once here; a test caught it.
#
# Sharing the counter also puts the limiter back in step with the
# account lockout: that has always been keyed on the email alone
# (_login_lockout_key), with no surface component, so 5 failures across
# both doors has always locked the account. The two layers now agree
# about what "5 attempts" means.
#
# Nothing changes for a mobile-only user: the allowance is still 5 per
# minute. Only someone hitting BOTH surfaces with the same email sees a
# difference, which is exactly the case this exists for.
LOGIN_SCOPE = "auth_login"

# REFRESH IS DELIBERATELY *NOT* SHARED. A supplier with the app in their
# pocket and the portal open on a laptop is two legitimate sessions, each
# renewing on its own schedule -- collapsing them into one 30/minute
# bucket would have the two clients throttle each other for no security
# gain. Refresh is also already authenticated: a caller must hold a
# valid refresh token to reach it at all, so it is not the door a
# credential-guessing attack comes through. Login is.
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
RATE_LIMIT_AUDIT_EVENTS: dict[str, AuthAuditEvent] = {
    "api.auth.login": AuthAuditEvent.LOGIN_RATE_LIMITED,
    "api.auth.register": AuthAuditEvent.REGISTER_RATE_LIMITED,
    "api.auth.refresh": AuthAuditEvent.REFRESH_RATE_LIMITED,
    "api.auth.forgot_password": AuthAuditEvent.PASSWORD_RESET_REQUEST_RATE_LIMITED,
    "api.auth.reset_password": AuthAuditEvent.PASSWORD_RESET_RATE_LIMITED,
    "api.auth.request_otp": AuthAuditEvent.OTP_REQUEST_RATE_LIMITED,
    "api.auth.verify_otp": AuthAuditEvent.OTP_VERIFY_RATE_LIMITED,
    # The web portal's own endpoints (V2 step 7). auth_web_bp is nested
    # in api_bp exactly as auth_bp is, so the same
    # "<parent>.<child>.<function>" naming applies -- these are
    # "api.auth_web.*", not "api.auth.*".
    #
    # WITHOUT THESE TWO LINES a rate-limit breach on the portal produces
    # the 429 and NO audit event: the limiter still works, but the
    # security stream never hears about it. That is the worst kind of
    # gap, because the thing that is broken is the thing you would use
    # to notice it. Same class of mistake as the endpoint-naming trap
    # recorded above.
    "api.auth_web.web_login": AuthAuditEvent.LOGIN_RATE_LIMITED,
    "api.auth_web.web_refresh": AuthAuditEvent.REFRESH_RATE_LIMITED,
}
