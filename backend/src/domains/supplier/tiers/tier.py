"""
Tier -- the supplier's own subscription tier concept. Small and stable
on purpose: this enum should change rarely (a new tier is a real
product decision), unlike the LIMITS each domain defines per tier,
which change often as numbers get tuned.

DELIBERATELY SEPARATE FROM domains/business/tiers/tier.py, NOT a
shared concept -- these are genuinely different products, sold to
different customer segments, with different pricing entirely. A
supplier's PRO plan (more product uploads, bigger bulk imports) has
nothing to do with a business's PRO plan (higher spending limits);
they only happened to share similar-sounding names. Sharing one enum
between them would make two unrelated subscriptions look like the same
thing at the type level -- confirmed as a real mistake after direct
review, corrected by keeping each role's tier concept fully
independent, even though the label vocabulary (FREE/PRO/MAX) looks
similar on both sides.

Room for ENTERPRISE deliberately left as a comment, not a speculative
member -- adding a value here is cheap the day it's real; guessing at
its shape now would just be a stale placeholder someone has to notice
and fix later.
"""
from __future__ import annotations

import enum


class Tier(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    MAX = "MAX"
    # ENTERPRISE = "ENTERPRISE"  -- add when it's a real, sold plan
