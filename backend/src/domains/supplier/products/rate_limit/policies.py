"""
Products' own rate-limit policies -- lives HERE, not in
security/rate_limit/, same domain-owns-its-own-policy split as
connections/rate_limit/policies.py (security owns the shared ENGINE,
each domain owns its own numbers).

Numbers below are Phase 1 starting points, same caveat every other
domain's own policies.py carries: NOT final production numbers, tune
once real traffic exists.

RATE_LIMIT_AUDIT_EVENTS gets registered in src/__init__.py alongside
every other domain's own mapping -- done in THIS SAME COMMIT, not
after, per the lesson from network/connections' own search_businesses
gap (a route that rate-limited correctly for a while with its audit
trail entry silently never recorded, because nobody had mapped it).
"""
from __future__ import annotations

from flask_jwt_extended import get_jwt_identity

from src.shared.audit.audit_types import AuditEventName

# --- Products limits (Phase 1) ------------------------------------------

PRODUCT_CREATE = "30 per minute"
PRODUCT_BULK_ACTION = "10 per minute"
MEDIA_SIGN = "20 per minute"


def supplier_key_func() -> str:
    """Keyed by the authenticated supplier's own identity -- every
    route in this domain requires a valid JWT already, same reasoning
    as connections' own business_key_func."""
    return get_jwt_identity() or "anonymous"


# Endpoint-name keys, NOT nested under "api." -- products_bp is
# registered directly on the app (matching connections_bp/loan_book_bp/
# order_book_bp's own pattern in src/__init__.py), so endpoint names
# are just "products.<view_function_name>".
RATE_LIMIT_AUDIT_EVENTS: dict[str, AuditEventName] = {
    "products.create_product": AuditEventName.PRODUCT_CREATE_RATE_LIMITED,
    "products.bulk_adjust_price": AuditEventName.PRODUCT_BULK_ACTION_RATE_LIMITED,
    "products.bulk_archive": AuditEventName.PRODUCT_BULK_ACTION_RATE_LIMITED,
    "products.request_media_upload_signature": AuditEventName.MEDIA_SIGN_RATE_LIMITED,
}
