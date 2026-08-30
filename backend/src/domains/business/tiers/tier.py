"""
BusinessTier -- the business role's own subscription tier concept.
Deliberately its OWN enum, not shared with domains/supplier/tiers/tier.py's
Tier -- see that file's own docstring for the full reasoning: these
are genuinely different products (a business's spending-limit
subscription has nothing to do with a supplier's upload-limit
subscription), and giving each role its own type is what keeps that
true at the type level, not just in comment prose.

Only FREE and PRO exist today, matching exactly what's been defined --
no speculative MAX or ENTERPRISE guessed at before either is a real,
sold plan for businesses.

STILL A REAL, LIVE CONCEPT EVEN THOUGH IT'S HIDDEN FROM THE APP TODAY
-- the frontend not yet exposing a way for a business to upgrade
doesn't mean this logic is speculative or deferred; a real business
may already be willing to pay, so the tier resolution and the
different spending limits it unlocks are built for real now (see
resolver.py's own docstring on what's actually reachable today versus
what's ready and waiting).
"""
from __future__ import annotations

import enum


class BusinessTier(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
