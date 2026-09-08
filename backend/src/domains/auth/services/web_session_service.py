"""
Web Session Service -- the browser half of authentication (V2 2.10).

WHAT THIS IS FOR
----------------
The supplier web portal. Not the mobile app, which keeps its JWT bearer
transport exactly as it is and is not touched by anything in this file.

WHY A BROWSER CANNOT DO WHAT THE APP DOES
------------------------------------------
The app stores a JWT and sends `Authorization: Bearer`. A browser must
not: anything reachable from JavaScript is reachable by any XSS on the
page, and a stolen JWT can be replayed from anywhere for as long as it
lives. An httpOnly cookie cannot be read by script at all. That does not
make XSS harmless -- injected script can still act as the user while the
tab is open -- but it removes the "exfiltrate a credential and use it
later, elsewhere" outcome, which is the one that turns a page bug into
an account takeover.

WHAT THIS FILE ACTUALLY OWNS
-----------------------------
Very little, and that is deliberate. Credential checking, lockout,
verification gating, refresh-token rotation and revocation all stay in
AuthService, because they are identical for both clients and a second
copy of a login flow is a second place for a security fix to be missed.
What is genuinely browser-specific is exactly three things:

  1. WHO IS ALLOWED IN (this portal serves suppliers; a business has no
     screens here at all),
  2. HOW LONG the session lives (config.py explains the numbers),
  3. GETTING THE TOKENS ONTO THE RESPONSE as cookies rather than JSON.

CSRF IS NOT HERE, ON PURPOSE
-----------------------------
Cookies are attached by the browser to any request, including one
triggered by someone else's page -- which is the whole reason bearer
tokens never needed CSRF protection and cookies do.
flask_jwt_extended's double-submit implementation is switched on in
config and enforced by the same `@jwt_required` the routes already use:
it issues a second, JS-READABLE cookie and demands the value back in the
X-CSRF-TOKEN header, which a cross-origin attacker cannot read. Writing
our own was rejected -- CSRF is a thing you get to be subtly wrong about
exactly once, and the library's version has the additional property of
applying ONLY to cookie-borne requests, so mobile is untouched.
"""
from __future__ import annotations

from typing import Optional, Tuple

from flask import Response, current_app
from flask_jwt_extended import set_access_cookies, set_refresh_cookies, unset_jwt_cookies

from src.domains.auth.models.user import User
from src.domains.auth.services.auth_service import AuthService

# The portal is the SUPPLIER's. Businesses buy stock from a phone in a
# shop; there is no business surface on the web at all, so letting one
# authenticate here would hand them a session with nothing behind it.
#
# A tuple rather than a hard-coded string because "admin" lands here the
# day the control centre exists, and that should be one entry rather
# than a new branch.
WEB_ALLOWED_ROLES = ("supplier",)

SESSION_KIND = "web"


class WebSessionService:
    @staticmethod
    def login(email: str, password: str, ip_address: Optional[str] = None) -> Tuple[User, dict]:
        """Delegates the entire hardened login path to AuthService and
        adds only the two web-specific parameters.

        NOTHING IS RE-IMPLEMENTED HERE. Lockout counting, the
        unverified-account sweep, the ACTIVE check and the audit trail
        are the same code the app runs through -- if a hole is ever
        found in one of them, there is one place to fix it.
        """
        return AuthService.login(
            email,
            password,
            ip_address=ip_address,
            allowed_roles=WEB_ALLOWED_ROLES,
            session_kind=SESSION_KIND,
        )

    @staticmethod
    def refresh(current_jti: str, user_id: str, ip_address: Optional[str] = None) -> dict:
        """Rotates the refresh token and re-issues the pair at web
        lifetimes. The rotation itself (revoke old, issue new, audit
        both) is AuthService's, unchanged."""
        return AuthService.refresh(
            current_jti=current_jti,
            user_id=user_id,
            ip_address=ip_address,
            session_kind=SESSION_KIND,
        )

    # ------------------------------------------------------------------
    # Cookie transport
    # ------------------------------------------------------------------

    @staticmethod
    def attach(response: Response, tokens: dict) -> Response:
        """Puts the freshly issued pair onto the response as cookies.

        MAX-AGE IS PASSED EXPLICITLY rather than left to the library,
        because flask_jwt_extended's default does not track the token
        at all: with JWT_SESSION_COOKIE at its default True it writes a
        SESSION cookie that dies when the browser closes, and with it
        False it writes a flat one-year cookie. Neither is the 7 days
        the refresh token inside actually lasts.

        The session-cookie default is the one that would have bitten:
        the supplier signs in, closes the browser at the end of the
        day, and is signed out tomorrow morning -- not because the
        session expired, but because the cookie carrying it was never
        written to disk. Passing max_age makes the cookie and the
        credential inside it expire together, which is the only
        arrangement that is honest to debug.
        """
        access_max_age = int(current_app.config["WEB_ACCESS_TOKEN_EXPIRES"].total_seconds())
        refresh_max_age = int(current_app.config["WEB_REFRESH_TOKEN_EXPIRES"].total_seconds())

        set_access_cookies(response, tokens["access_token"], max_age=access_max_age)
        set_refresh_cookies(response, tokens["refresh_token"], max_age=refresh_max_age)
        return response

    @staticmethod
    def clear(response: Response) -> Response:
        """Removes all four cookies -- both tokens AND both CSRF
        companions. Leaving a stale CSRF cookie behind is harmless for
        security but makes the next sign-in read a value that no longer
        pairs with anything, which is a confusing failure to debug."""
        unset_jwt_cookies(response)
        return response
