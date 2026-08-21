"""
get_current_tier -- the ONE function every domain calls to find out
what tier a supplier is actually on. Deliberately isolated to this one
function: there is no real Subscription/billing model on this backend
yet, so this always returns FREE today -- same "honest about today's
reality" pattern already used throughout this codebase (see products/
services/product_media_service.py's own tier-honesty note, written
before this resolver existed). The day a real Subscription domain
exists, THIS is the only place that needs to change; every caller
(product_media_service, import_worker, etc.) already calls this
function rather than hardcoding "FREE" themselves.
"""
from __future__ import annotations

from uuid import UUID

from src.domains.supplier.tiers.tier import Tier


def get_current_tier(supplier_profile_id: str | UUID) -> Tier:
    return Tier.FREE
