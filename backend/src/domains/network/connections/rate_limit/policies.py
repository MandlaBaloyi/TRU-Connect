"""
Supplier Discovery's own rate-limit policies -- lives HERE, not in
security/rate_limit/, same domain-owns-its-own-policy split as
auth/rate_limit/policies.py (security owns the shared ENGINE, each
domain owns its own numbers). Fills in loan_book/rate_limit/policies.py's
own "NOT IMPLEMENTED YET" stub shape for real, for this domain.

Numbers below are Phase 1 starting points, same caveat as auth's own
policies.py: NOT final production numbers, tune once real traffic
exists.
"""
from __future__ import annotations

from flask_jwt_extended import get_jwt_identity

from src.shared.audit.audit_types import AuditEventName

# --- Supplier Discovery limits (Phase 1) --------------------------------

SEARCH = "30 per minute"
CONNECTION_REQUEST = "10 per hour"


def business_key_func() -> str:
    """Keyed by the authenticated business's own identity, not IP --
    unlike login (auth/rate_limit/policies.py's login_key_func), every
    route in this domain requires a valid JWT already, so there's a
    real identity to key by directly. This means one business's search
    activity never affects another business sharing the same network
    (same reasoning auth's login_key_func documents for why IP-alone
    would be wrong there too, applied here with an even better key
    available).
    """
    return get_jwt_identity() or "anonymous"


# Endpoint-name keys, NOT nested under "api." -- unlike auth_bp (nested
# inside api_bp, so Flask's endpoint names chain as "api.auth.login"),
# connections_bp is registered directly on the app (matching
# loan_book_bp/order_book_bp/business_profile_bp's own pattern in
# src/__init__.py), so its endpoint names are just
# "connections.<view_function_name>", confirmed by how those
# three existing blueprints are actually registered.
RATE_LIMIT_AUDIT_EVENTS: dict[str, AuditEventName] = {
    "connections.search": AuditEventName.SUPPLIER_SEARCH_RATE_LIMITED,
    "connections.request_connection": AuditEventName.CONNECTION_REQUEST_RATE_LIMITED,
    # Find Business's own search route (supplier -> business direction).
    # Previously unmapped: the 429 response itself always fired correctly
    # (rate limiting worked), but the audit trail entry for that specific
    # violation was silently never recorded, because
    # _AUDIT_EVENT_REGISTRY.get(request.endpoint) returned None for this
    # endpoint and responses.py's handler skips logging when that happens
    # (correct, safe behaviour for a genuinely-unmapped endpoint -- this
    # endpoint just should have been mapped from the start).
    "connections.search_businesses": AuditEventName.BUSINESS_SEARCH_RATE_LIMITED,
}
