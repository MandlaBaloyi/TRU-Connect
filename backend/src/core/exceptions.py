"""
Custom exception hierarchy.
Ref: backend master prompt, "Proper exception handling"; Auth Hardening
master prompt, Objective 1 (structured error codes).

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
    """Ref: Auth Hardening master prompt, Objective 1, Rule 3."""

    code = "EMAIL_NOT_VERIFIED"


class AccountInactiveError(ForbiddenError):
    code = "ACCOUNT_INACTIVE"


class AccountLockedError(AppError):
    """Ref: Auth Hardening master prompt, Objective 9 -- temporary
    lockout after repeated failed login attempts."""

    status_code = 423  # Locked
    code = "ACCOUNT_LOCKED"


class TicketInvalidError(UnauthorizedError):
    """Ref: Auth Hardening master prompt, Objectives 4/5/7 -- password
    reset (and future magic-link/invitation) ticket flows."""

    code = "TICKET_INVALID"
