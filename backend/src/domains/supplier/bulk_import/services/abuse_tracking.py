"""
Bulk Import's own abuse-lockout mechanism -- same underlying
RateLimitCache abstraction (see shared/cache/cache.py's own docstring)
already powering login lockout in auth_service.py, reused here rather
than reinvented. Swaps to a real Redis-backed cache automatically, for
free, the moment cache.py's own single swap point does -- this file
never talks to InMemoryCache directly.

ONLY is_malicious=True VIOLATIONS COUNT -- see zip_parser.py's own
UnsafeZipError docstring for the full reasoning on exactly why path
traversal and a suspicious compression ratio are the only two things
treated as a genuine, no-honest-explanation attack signal. Every other
validation error a supplier can hit (wrong column names, a row
referencing a missing photo, going over their plan's row/photo limit,
a corrupted upload, too many files, a single file over the size
ceiling, an unsupported file type) is completely normal, happens to
honest suppliers constantly, and must NEVER be passed to
record_violation.

LOCKS THE FEATURE, NOT THE ACCOUNT -- deliberately. A supplier hitting
this can still do everything else in the app, including adding
products one at a time. If this is ever wrong about someone (a false
positive), the cost of that mistake stays small and recoverable,
rather than locking them out of their whole business.
"""
from __future__ import annotations

import os

from src.shared.audit.audit import publish
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditStatus
from src.shared.audit.event_types.supplier import SupplierAuditEvent
from src.shared.cache.cache import cache

# Real security-policy values, not per-environment facts -- same
# "constant with an optional env override" pattern already used for
# LOGIN_MAX_FAILED_ATTEMPTS/LOGIN_LOCKOUT_WINDOW_MINUTES. The real
# number lives here, in code, reviewed like any other decision; .env
# only needs touching if THIS environment genuinely needs to differ.
MAX_VIOLATIONS = int(os.environ.get("BULK_IMPORT_MAX_VIOLATIONS", "3"))
LOCKOUT_WINDOW_MINUTES = int(os.environ.get("BULK_IMPORT_LOCKOUT_WINDOW_MINUTES", "60"))


def _violation_key(supplier_profile_id) -> str:
    return f"bulk_import_violations:{supplier_profile_id}"


def is_locked_out(supplier_profile_id) -> bool:
    """Read-only -- does NOT increment. Same "check without touching
    the counter" access pattern login lockout already uses (see
    cache.py's own docstring on why get_count()/increment() are kept
    as separate primitives)."""
    return cache.get_count(_violation_key(supplier_profile_id)) >= MAX_VIOLATIONS


def record_violation(supplier_profile_id) -> None:
    """Call ONLY when a caught UnsafeZipError's own is_malicious flag
    is True -- never for an ordinary validation failure. Publishes its
    own audit event every time, separate from (and in addition to) the
    one-time lockout-reached event below, so a security review can see
    every individual violation, not just the moment the threshold hit."""
    count = cache.increment(_violation_key(supplier_profile_id), ttl_seconds=LOCKOUT_WINDOW_MINUTES * 60)

    publish(
        AuditEvent(
            event_name=SupplierAuditEvent.BULK_IMPORT_SUSPICIOUS_FILE_DETECTED,
            domain=AuditDomain.SUPPLIER,
            status=AuditStatus.FAILURE,
            metadata={"supplier_profile_id": str(supplier_profile_id), "violation_count": count},
        )
    )

    if count >= MAX_VIOLATIONS:
        publish(
            AuditEvent(
                event_name=SupplierAuditEvent.BULK_IMPORT_LOCKED_OUT,
                domain=AuditDomain.SUPPLIER,
                status=AuditStatus.FAILURE,
                metadata={
                    "supplier_profile_id": str(supplier_profile_id),
                    "lockout_window_minutes": LOCKOUT_WINDOW_MINUTES,
                },
            )
        )
