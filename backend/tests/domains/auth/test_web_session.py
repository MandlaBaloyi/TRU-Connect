"""
Web portal session tests (V2 2.10).

WHAT THESE ARE ACTUALLY GUARDING. Not "does login return 200" -- the
four properties that make a cookie session safe, each of which is
invisible in a passing manual test:

  1. The credential is in an httpOnly cookie and NOT in the response
     body. A body copy would defeat the entire reason for the cookie,
     and is the kind of thing added later "for debugging".
  2. CSRF is actually enforced on cookie-borne writes. A misconfigured
     double-submit fails OPEN -- everything works, nothing is protected.
  3. A `business` cannot get a portal session at all.
  4. The mobile bearer path still works, unchanged, now that the app
     also accepts cookies.

Number 4 is the regression this whole step could plausibly cause, so it
is tested here rather than trusted.
"""
from __future__ import annotations

import pytest

from src.domains.auth.models.user import AccountStatus, UserRole, VerificationStatus
from src.extensions import db

PASSWORD = "Abcd1234!"

WEB = "/api/v1/auth/web"
MOBILE = "/api/v1/auth"


@pytest.fixture()
def supplier(make_user):
    user = make_user(
        "supplier@example.com",
        password=PASSWORD,
        role=UserRole.SUPPLIER,
        verification_status=VerificationStatus.VERIFIED,
        account_status=AccountStatus.ACTIVE,
        business_name="MacMan Wholesalers",
    )
    db.session.commit()
    return user


@pytest.fixture()
def business(make_user):
    user = make_user(
        "business@example.com",
        password=PASSWORD,
        role=UserRole.BUSINESS,
        verification_status=VerificationStatus.VERIFIED,
        account_status=AccountStatus.ACTIVE,
    )
    db.session.commit()
    return user


# ONLY refresh_token_cookie lives at the scoped path. Its CSRF companion
# csrf_refresh_token is issued at "/" -- deliberately, by the library:
# the portal's JavaScript has to be able to read that value from any
# page in order to echo it back, and a cookie scoped to /api/v1/auth/web
# is not readable from a page at /catalogue.
#
# Worth spelling out because the two names look like a pair and are not,
# and a get_cookie at the wrong path returns None, which reads exactly
# like "the cookie was never set".
REFRESH_PATH = "/api/v1/auth/web"
SCOPED_COOKIES = {"refresh_token_cookie"}


def _cookie(client, name):
    """Returns the cookie's VALUE, or None. get_cookie hands back a
    Cookie object; passing that object straight into a header stringifies
    its repr, which then fails the CSRF comparison for reasons that look
    nothing like the actual cause."""
    path = REFRESH_PATH if name in SCOPED_COOKIES else "/"
    cookie = client.get_cookie(name, path=path)
    return cookie.value if cookie is not None else None


# ---------------------------------------------------------------------
# Sign in
# ---------------------------------------------------------------------

def test_web_login_sets_cookies_and_never_returns_the_token(client, supplier):
    response = client.post(
        f"{WEB}/login", json={"email": supplier.email, "password": PASSWORD}
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True

    # THE ASSERTION THAT MATTERS. Serialising the whole body and
    # searching it, rather than checking a couple of known key names --
    # a token leaking through some nested field is exactly the case a
    # targeted check would miss.
    assert "access_token" not in str(body)
    assert "refresh_token" not in str(body)
    assert body["data"]["user"]["email"] == supplier.email

    access = _cookie(client, "access_token_cookie")
    refresh = _cookie(client, "refresh_token_cookie")
    assert access is not None
    assert refresh is not None

    # httpOnly is the whole point: script on the page must not be able
    # to read these.
    set_cookie_headers = " ".join(response.headers.getlist("Set-Cookie"))
    assert "HttpOnly" in set_cookie_headers

    # The CSRF companions are deliberately NOT httpOnly -- the portal's
    # own JavaScript has to read them to echo the value back.
    assert _cookie(client, "csrf_access_token") is not None
    assert _cookie(client, "csrf_refresh_token") is not None


def test_refresh_cookie_is_scoped_to_the_auth_routes(client, supplier):
    """The long-lived credential should not ride along on every ordinary
    API call -- only on the handful of routes that can use it."""
    response = client.post(
        f"{WEB}/login", json={"email": supplier.email, "password": PASSWORD}
    )
    refresh_header = next(
        h for h in response.headers.getlist("Set-Cookie") if h.startswith("refresh_token_cookie=")
    )
    assert f"Path={REFRESH_PATH}" in refresh_header


def test_business_cannot_sign_in_to_the_supplier_portal(client, business):
    response = client.post(
        f"{WEB}/login", json={"email": business.email, "password": PASSWORD}
    )

    assert response.status_code == 403
    body = response.get_json()
    # A DISTINCT CODE, not a generic 403 -- the client can only send
    # them to the app if it can tell this apart from every other refusal.
    assert body["code"] == "WRONG_PORTAL"
    # And no session was created on the way to being refused.
    assert _cookie(client, "access_token_cookie") is None


def test_wrong_password_does_not_reveal_the_portal_rule(client, business):
    """A business with the WRONG password must look identical to any
    other bad credential -- the role check runs after the password, so
    an anonymous caller cannot use this endpoint to discover which
    emails are business accounts."""
    response = client.post(
        f"{WEB}/login", json={"email": business.email, "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert response.get_json().get("code") != "WRONG_PORTAL"


# ---------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------

def test_cookie_write_without_the_csrf_header_is_rejected(client, supplier):
    """The failure mode this guards is silent: a broken double-submit
    config lets every request through and nothing looks wrong."""
    client.post(f"{WEB}/login", json={"email": supplier.email, "password": PASSWORD})

    response = client.post(f"{WEB}/refresh")

    assert response.status_code == 401


def test_cookie_write_with_the_csrf_header_succeeds(client, supplier):
    client.post(f"{WEB}/login", json={"email": supplier.email, "password": PASSWORD})
    csrf = _cookie(client, "csrf_refresh_token")

    response = client.post(f"{WEB}/refresh", headers={"X-CSRF-TOKEN": csrf})

    assert response.status_code == 200
    assert "access_token" not in str(response.get_json())


# ---------------------------------------------------------------------
# Session read + sign out
# ---------------------------------------------------------------------

def test_session_endpoint_identifies_the_cookie_holder(client, supplier):
    client.post(f"{WEB}/login", json={"email": supplier.email, "password": PASSWORD})

    response = client.get(f"{WEB}/session")

    assert response.status_code == 200
    assert response.get_json()["data"]["user"]["email"] == supplier.email


def test_session_endpoint_401s_without_a_cookie(client):
    assert client.get(f"{WEB}/session").status_code == 401


def test_logout_clears_the_cookies(client, supplier):
    client.post(f"{WEB}/login", json={"email": supplier.email, "password": PASSWORD})
    csrf = _cookie(client, "csrf_refresh_token")

    response = client.post(f"{WEB}/logout", headers={"X-CSRF-TOKEN": csrf})

    assert response.status_code == 200
    assert _cookie(client, "access_token_cookie") is None
    assert _cookie(client, "refresh_token_cookie") is None
    assert client.get(f"{WEB}/session").status_code == 401


def test_logout_succeeds_even_with_no_session(client):
    """Signing out must never fail. The case that matters is a stale tab
    whose session already expired -- the exact moment a user reaches for
    the button is the moment a strict handler would 401 and leave the
    cookies in place."""
    assert client.post(f"{WEB}/logout").status_code == 200


# ---------------------------------------------------------------------
# The regression this step could actually cause
# ---------------------------------------------------------------------

def test_mobile_bearer_login_is_unchanged(client, supplier):
    """JWT_TOKEN_LOCATION now lists cookies as well as headers. This
    asserts that adding it did not disturb the shipped app's contract:
    tokens still come back in the body, and a bearer header still
    authenticates."""
    response = client.post(
        f"{MOBILE}/login", json={"email": supplier.email, "password": PASSWORD}
    )

    assert response.status_code == 200
    tokens = response.get_json()["data"]["tokens"]
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me = client.get(
        f"{MOBILE}/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200
    assert me.get_json()["data"]["email"] == supplier.email


def test_mobile_business_login_still_works(client, business):
    """The portal's role gate must not have leaked into the app -- a
    business signing into the MOBILE app is the single most common
    login in the product."""
    response = client.post(
        f"{MOBILE}/login", json={"email": business.email, "password": PASSWORD}
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["tokens"]["access_token"]


def test_bearer_requests_need_no_csrf_header(client, supplier):
    """CSRF applies only to cookie-borne requests. If it ever applied to
    bearer requests, every mobile write in the app would break at
    once."""
    login = client.post(f"{MOBILE}/login", json={"email": supplier.email, "password": PASSWORD})
    access = login.get_json()["data"]["tokens"]["access_token"]

    response = client.patch(
        f"{MOBILE}/me/profile-image",
        headers={"Authorization": f"Bearer {access}"},
        json={"imageUrl": None},
    )

    assert response.status_code != 401


def test_cookies_are_marked_secure_when_configured(app, client, supplier):
    """The flag that only matters in production, and is therefore the
    one no manual test ever exercises.

    Dev and test force JWT_COOKIE_SECURE off because both speak http --
    a Secure cookie is simply never sent over a plain connection, so
    leaving it on locally makes sign-in fail silently. That override is
    also why nothing else here would notice if the production path
    stopped setting it. Flipped deliberately for this one test.
    """
    app.config["JWT_COOKIE_SECURE"] = True
    try:
        response = client.post(
            f"{WEB}/login", json={"email": supplier.email, "password": PASSWORD}
        )
    finally:
        app.config["JWT_COOKIE_SECURE"] = False

    session_cookie = next(
        h for h in response.headers.getlist("Set-Cookie") if h.startswith("access_token_cookie=")
    )
    assert "Secure" in session_cookie
    assert "HttpOnly" in session_cookie
    assert "SameSite=Lax" in session_cookie


# ---------------------------------------------------------------------
# Rate limiting across both surfaces
# ---------------------------------------------------------------------

def test_login_rate_limit_is_shared_between_the_app_and_the_portal(client):
    """Five attempts a minute against an email, not five per door.

    THE BUG THIS PINS. Flask-Limiter buckets per ENDPOINT by default, so
    adding a second login route silently doubled the allowance: five
    tries at /auth/login and five more at /auth/web/login, from a policy
    that reads "5 per minute" and looks entirely correct. Nothing in
    either decorator would have looked wrong in review.

    The assertion is specifically 429 AND NOT 423. Both are refusals, so
    a test that merely checked "the sixth attempt fails" would have
    passed before the fix too -- the account lockout would have caught
    it a moment later and returned 423 instead. Only the 429 proves the
    LIMITER shared its counter.

    Uses an address with no account: a failed login is a failed login as
    far as both throttles are concerned, and this keeps the test clear
    of lockout semantics on a real user.
    """
    email = "nobody-here@example.com"
    body = {"email": email, "password": "wrong-password"}

    # Five attempts, split across the two surfaces.
    statuses = [
        client.post(f"{MOBILE}/login", json=body).status_code,
        client.post(f"{WEB}/login", json=body).status_code,
        client.post(f"{MOBILE}/login", json=body).status_code,
        client.post(f"{WEB}/login", json=body).status_code,
        client.post(f"{MOBILE}/login", json=body).status_code,
    ]
    assert 429 not in statuses, f"limiter fired early: {statuses}"

    # The sixth is over the shared limit, whichever door it knocks on.
    assert client.post(f"{WEB}/login", json=body).status_code == 429
