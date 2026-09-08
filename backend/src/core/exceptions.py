"""
Custom exception hierarchy.
"Proper exception handling"
(structured error codes).

Services raise these instead of returning ad-hoc error tuples; the app
factory's single error handler converts any AppError into the standard
JSON envelope automatically -- routes never need to catch these
individually.

`code` and `data` are new, optional, additive fields. `code` is a stable,
machine-readable string (e.g. "EMAIL_NOT_VERIFIED") the frontend can
switch on instead of parsing the human-readable message. `data` carries
structured metadata alongside a failure (e.g. resend availability).
"""
from __future__ import annotations

from typing import Optional


class AppError(Exception):
    """Base class for all application-level errors."""

    status_code = 400
    code: Optional[str] = None

    def __init__(
        self,
        message: str,
        errors: Optional[list] = None,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        data: Optional[dict] = None,
    ):
        super().__init__(message)
        self.message = message
        self.errors = errors or []
        self.data = data
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class NotFoundError(AppError):
    status_code = 404


class ValidationError(AppError):
    status_code = 422


class ConflictError(AppError):
    status_code = 409


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class EmailNotVerifiedError(ForbiddenError):
    """ Auth Hardening ."""

    code = "EMAIL_NOT_VERIFIED"


class AccountInactiveError(ForbiddenError):
    code = "ACCOUNT_INACTIVE"


class AccountLockedError(AppError):
    """ Auth Hardening  -- temporary
    lockout after repeated failed login attempts."""

    status_code = 423  # Locked
    code = "ACCOUNT_LOCKED"


class TicketInvalidError(UnauthorizedError):
    """-- password
    reset (and future magic-link/invitation) ticket flows."""

    code = "TICKET_INVALID"


class WrongPortalError(ForbiddenError):
    """The credentials are correct, but this account belongs on a
    different surface -- today: a `business` signing in at the supplier
    web portal, which has no business screens at all (V2 2.10, "role
    routing").

    ITS OWN CODE RATHER THAN A GENERIC 403 because the only useful
    response is not "you may not do that" but "your side of TruConnect
    is the app, here is where to get it" -- and the web client can only
    say that if it can tell this apart from every other refusal. A
    correct password answered with "invalid email or password" would be
    a small lie that costs a real supplier-adjacent user ten minutes.
    """

    code = "WRONG_PORTAL"


class InvalidApiKeyError(UnauthorizedError):
    """A machine credential that is missing, malformed, unknown,
    revoked, or expired.

    ONE ERROR FOR ALL FIVE CASES, deliberately. Telling an unauthenticated
    caller *which* of those it is confirms that a key exists, or that it
    once did -- free reconnaissance in exchange for a debugging
    convenience that the key's owner can get from their own portal
    screen, where we know who they are.
    """

    code = "INVALID_API_KEY"


class ApiKeyScopeError(ForbiddenError):
    """A valid key that is not permitted to do this.

    Distinct from InvalidApiKeyError because the caller IS
    authenticated: they are a known supplier's integration, and telling
    them their key lacks `catalogue:write` leaks nothing they do not
    already own. It is also the single most common integration mistake,
    and a specific message is what turns a support email into a
    self-service fix.
    """

    code = "API_KEY_SCOPE"
