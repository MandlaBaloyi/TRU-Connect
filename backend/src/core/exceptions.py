"""
Custom exception hierarchy.
Ref: backend master prompt, "Proper exception handling" -- services raise
these instead of returning ad-hoc error tuples; the app factory's single
error handler (src/__init__.py) converts any AppError into the standard
JSON envelope (src/core/responses.py) automatically. Routes never need to
catch these individually.
"""
from __future__ import annotations


class AppError(Exception):
    """Base class for all application-level errors."""

    status_code = 400

    def __init__(self, message: str, errors: list | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404


class ValidationError(AppError):
    """Distinct from Marshmallow's own ValidationError -- this is the
    application-level error a service raises after Marshmallow validation
    has already passed but a business rule still fails (e.g.
    docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt constraints)."""
    status_code = 422


class ConflictError(AppError):
    """E.g. duplicate email registration attempt -- docs/06, Section 1."""
    status_code = 409


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    """E.g. a business-role token calling a supplier-only route --
    docs/05_BACKEND_API_SPECIFICATION.txt, Section 14 (Role-Based Access
    Summary)."""
    status_code = 403
