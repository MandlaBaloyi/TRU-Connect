"""
Catalogue's own audit vocabulary -- decisions about what a product IS.

WHY A MATCH DECISION IS AN AUDITABLE EVENT and not just a row in
match_reviews. Accepting a proposal does not change one supplier's
offer; it writes a GLOBAL ALIAS, so from then on any supplier who
types those same words is matched automatically, forever. The blast
radius is every supplier on the platform.

match_reviews already records decided_by_user_id and decided_at, which
is the operational record. This is the SECURITY record: it sits in the
same table as every other privileged act, so "what did this staff
member do" is one query rather than a tour of per-domain tables
somebody has to know exist.
"""
from __future__ import annotations

import enum


class CatalogueAuditEvent(str, enum.Enum):
    MATCH_ACCEPTED = "catalogue.match_accepted"
    MATCH_REJECTED = "catalogue.match_rejected"
