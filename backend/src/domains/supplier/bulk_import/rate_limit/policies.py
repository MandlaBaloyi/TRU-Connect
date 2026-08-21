"""
Bulk Import's own rate-limit policies. Same domain-owns-its-own-policy
split as every other domain in this codebase.

5 per hour, not per minute -- this is a genuinely heavy operation
(potentially thousands of product creations + image uploads), unlike
everything else this app rate-limits by the minute.
"""
from __future__ import annotations

from flask_jwt_extended import get_jwt_identity

from src.shared.audit.audit_types import AuditEventName

BULK_IMPORT_SUBMIT = "5 per hour"


def supplier_key_func() -> str:
    return get_jwt_identity() or "anonymous"


RATE_LIMIT_AUDIT_EVENTS: dict[str, AuditEventName] = {
    "bulk_import.submit_import": AuditEventName.BULK_IMPORT_SUBMIT_RATE_LIMITED,
}
