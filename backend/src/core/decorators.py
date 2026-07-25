"""
Authorization decorators.
Ref: continuation master prompt, Step 10 (role_required) and Step 15
(permission_required) -- "Authorization must remain independent from
authentication... Create reusable decorators... Support Role validation,
Permission validation, Future granular permissions."
"""
from __future__ import annotations

from functools import wraps

from flask_jwt_extended import get_jwt, jwt_required

from src.core.exceptions import ForbiddenError


def role_required(*allowed_roles: str):
    """Stacks JWT verification + role authorization in one decorator.

        @some_bp.get("/business-only-thing")
        @role_required("business")
        def business_only_thing():
            ...

    Multiple roles may be passed (e.g. @role_required("business", "admin")).
    Supports every role in UserRole (business, supplier, admin) and any
    future role added to that enum without this decorator changing.
    """

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
    """STRUCTURAL PLACEHOLDER for granular, permission-level
    authorization (Step 15: "Future granular permissions"). No
    Permission/RolePermission model exists yet -- there is nowhere to
    look up what permissions a role actually grants. This decorator
    checks for a "permissions" JWT claim, which nothing currently
    populates, so as written it will deny access to everything until:

      1. A Permission model + role-to-permission mapping is built, and
      2. AuthService._issue_tokens is updated to include a resolved
         "permissions" list in additional_claims.

    Included now so route signatures that will eventually need
    permission checks (rather than just role checks) can be written
    against this decorator today, without every call site needing to
    change later -- only this function's internals do.
    """

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
