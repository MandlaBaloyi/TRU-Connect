"""
Authorization decorators.
 (role_required,
permission_required ),
Objective 3 (login_required, verified_required, active_account_required,
fully_authenticated -- NEW).

verified_required / active_account_required / fully_authenticated
deliberately RE-CHECK THE DATABASE on every request rather than trusting
a JWT claim. A claim baked into a token at issue time cannot reflect a
status that changes afterwards (e.g. an account verified, or
deactivated, after its current token was already issued) without an
explicit token re-issue -- a database check is what actually closes
that gap, at the cost of one extra query per protected request.
"""
from __future__ import annotations

from functools import wraps

from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from src.core.exceptions import AccountInactiveError, EmailNotVerifiedError, ForbiddenError


def _load_current_user():
    """Local import avoids a circular import between core (imported very
    early, by the app factory) and the auth domain."""
    from src.domains.auth.repositories.user_repository import UserRepository

    return UserRepository.get_by_id(get_jwt_identity())


def login_required(fn):
    """Thin, explicitly-named wrapper around flask_jwt_extended's
    jwt_required() -- exists so route declarations read @login_required
    rather than a raw library call, and so future session/audit hooks
    have one place to attach to."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def verified_required(fn):
    """Requires authentication AND a current, database-fresh
    verification_status == VERIFIED. This is the decorator that closes
    the "a valid token from an unverified account can still be used"
    hole -- apply it to any endpoint an unverified user must not reach."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from src.domains.auth.models.user import VerificationStatus

        user = _load_current_user()
        if user is None or user.verification_status != VerificationStatus.VERIFIED:
            raise EmailNotVerifiedError("Please verify your email before continuing.")
        return fn(*args, **kwargs)

    return wrapper


def active_account_required(fn):
    """Requires authentication and account_status == ACTIVE."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from src.domains.auth.models.user import AccountStatus

        user = _load_current_user()
        if user is None or user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account is not active.")
        return fn(*args, **kwargs)

    return wrapper


def fully_authenticated(fn):
    """Convenience combination: authenticated + verified + active, in
    ONE decorator and ONE database lookup, for the common case (Auth
    Hardening, Objective 3 examples: /dashboard, /orders,
    /profile, /catalogue, /notifications)."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from src.domains.auth.models.user import AccountStatus, VerificationStatus

        user = _load_current_user()
        if user is None or user.verification_status != VerificationStatus.VERIFIED:
            raise EmailNotVerifiedError("Please verify your email before continuing.")
        if user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account is not active.")
        return fn(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles: str):
    """
    Stacks JWT verification + role authorization in one decorator.
    Supports every role in UserRole and any future role added to that
    enum without this decorator changing."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                raise ForbiddenError("You do not have permission to access this resource.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def permission_required(*required_permissions: str):
    """UNCHANGED -- structural placeholder for granular permissions;
     for the full rationale."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            granted = set(claims.get("permissions", []))
            if not set(required_permissions).issubset(granted):
                raise ForbiddenError("You do not have permission to access this resource.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
