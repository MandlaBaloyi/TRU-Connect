"""
Per-domain audit event vocabularies -- one small file per domain that
actually publishes events today, replacing the single 89-line flat
AuditEventName enum this package used to be an unused placeholder
next to. Re-exported here so `from src.shared.audit.event_types import
AuthAuditEvent` works alongside importing each domain's own module
directly -- callers use whichever reads better at the call site.
"""
from __future__ import annotations

from src.shared.audit.event_types.admin import AdminAuditEvent
from src.shared.audit.event_types.auth import AuthAuditEvent
from src.shared.audit.event_types.catalogue import CatalogueAuditEvent
from src.shared.audit.event_types.network import NetworkAuditEvent
from src.shared.audit.event_types.platform import PlatformAuditEvent
from src.shared.audit.event_types.supplier import SupplierAuditEvent
from src.shared.audit.event_types.verification import VerificationAuditEvent

__all__ = [
    "AdminAuditEvent",
    "AuthAuditEvent",
    "CatalogueAuditEvent",
    "NetworkAuditEvent",
    "PlatformAuditEvent",
    "SupplierAuditEvent",
    "VerificationAuditEvent",
]
