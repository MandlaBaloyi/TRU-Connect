"""
Verification's own audit event vocabulary, same per-domain split as
event_types/auth.py and event_types/supplier.py.

WHY VERIFICATION AUDITS AT ALL, WHILE IT STILL HOLDS NO DOCUMENTS.
A verification decision is the single act on this platform that turns a
supplier from invisible into somebody a business will hand money to.
"Who decided this, and on what grounds" is the question asked after
something goes wrong, and a decision made by a human at a terminal
leaves no other trace.

VERIFICATION_DOCUMENT_VIEWED is declared here ahead of the feature it
belongs to (V2_12 Phase 2). Reading somebody's identity document is a
privileged act that must be logged as its own event -- not folded into
the decision -- because "who looked at this person's ID" and "who
approved this supplier" are different questions, and only the first
one can be answered after a leak.
"""
from __future__ import annotations

import enum


class VerificationAuditEvent(str, enum.Enum):
    SUPPLIER_APPROVED = "verification.supplier_approved"
    SUPPLIER_REVOKED = "verification.supplier_revoked"
    # Phase 2 -- declared, not yet published by anything.
    DOCUMENT_VIEWED = "verification.document_viewed"
    DOCUMENT_DELETED = "verification.document_deleted"
