"""
Tier -- the subscription tier concept itself. Small and stable on
purpose: this enum should change rarely (a new tier is a real product
decision), unlike the LIMITS each domain defines per tier, which
change often as numbers get tuned.

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
