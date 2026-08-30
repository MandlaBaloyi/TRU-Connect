"""
get_current_tier -- the ONE function every business-side domain calls
to find out what tier a business is actually on. Deliberately isolated
to this one function: there is no real Subscription/billing model on
this backend yet, so this always returns FREE today -- same honest
pattern as domains/supplier/tiers/resolver.py's own version (that
file's docstring explains the reasoning in full; this mirrors the
PHILOSOPHY for the business role, using BusinessTier -- its own,
independent type, never the supplier's Tier).

The day a real Subscription domain exists, THIS is the only place
that needs to change -- every caller (domains/business/stock_order's
own checkout_service.py, and anything else that needs a business's
tier later) already calls this function rather than hardcoding "FREE"
themselves.
"""
from __future__ import annotations

from uuid import UUID

from src.domains.business.tiers.tier import BusinessTier


def get_current_tier(business_id: str | UUID) -> BusinessTier:
    return BusinessTier.FREE
