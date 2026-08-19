"""
Inventory's own rate-limit policies. Same domain-owns-its-own-policy
split as products/rate_limit/policies.py.

RATE_LIMIT_AUDIT_EVENTS registered in src/__init__.py in the SAME
commit as the blueprint, per the connections/search_businesses lesson
(see products/rate_limit/policies.py's own docstring for the full
reasoning).
"""
from __future__ import annotations

from flask_jwt_extended import get_jwt_identity

from src.shared.audit.audit_types import AuditEventName

INVENTORY_ADJUST = "20 per minute"


def supplier_key_func() -> str:
    return get_jwt_identity() or "anonymous"


# inventory_bp registered directly on the app (same pattern as
# products_bp/connections_bp) -- endpoint names are just
# "inventory.<view_function_name>".
RATE_LIMIT_AUDIT_EVENTS: dict[str, AuditEventName] = {
    "inventory.adjust_stock": AuditEventName.INVENTORY_ADJUST_RATE_LIMITED,
}
