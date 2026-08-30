"""
stock_order's own rate-limit policies -- lives HERE, not in
security/rate_limit/, same domain-owns-its-own-policy split as
network/connections/rate_limit/policies.py's own docstring explains in
full (security owns the shared ENGINE, each domain owns its own
numbers).

submit_checkout moves real money and now enforces real tier-based
spending limits a bad actor might want to probe -- rate limiting it is
worth doing for the same reason connections' own search endpoints are
limited, not a new idea invented for this domain.

Numbers below are Phase 1 starting points, same caveat as every other
domain's own policies.py: NOT final production numbers, tune once
real traffic exists.
"""
from __future__ import annotations

from flask_jwt_extended import get_jwt_identity

from src.shared.audit.event_types.business import BusinessAuditEvent

SUBMIT_CHECKOUT = "20 per hour"


def business_key_func() -> str:
    """Keyed by the authenticated business's own identity, not IP --
    every route in this domain requires a valid JWT already, same
    reasoning as connections/rate_limit/policies.py's own
    business_key_func."""
    return get_jwt_identity() or "anonymous"


# Endpoint-name keys, matching how orders_bp is registered directly on
# the app (src/__init__.py) -- its endpoint names are
# "orders.<view_function_name>", same shape as connections_bp's own
# precedent.
RATE_LIMIT_AUDIT_EVENTS = {
    "orders.submit_checkout": BusinessAuditEvent.CHECKOUT_RATE_LIMITED,
}
