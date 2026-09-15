"""
What a supplier's plan actually moves.

THE RULE, IN ONE SENTENCE (V2_16, V2_17):

    TIER MAY BREAK A TIE. IT MAY NEVER BEAT A FACT.

THIS MODULE LIVES OUTSIDE demand/ ON PURPOSE, and the architecture
tests enforce it both ways: the demand engine may not read a plan, and
nothing here may read the demand engine. The feed composer sits between
them and is the only thing allowed to know both -- what a shop needs,
and who is paying for reach.

WHAT MONEY MAY NOT TOUCH, restated here because this is the file
somebody will edit when they want it to:

    buy it again            the shop's own confirmed history
    stock for your shop     the demand engine's answer
    moving fast             measured velocity
    offer_selection         whose offer wins for a product they
                            already want
    collect near you        ranked strictly by distance, because the
                            card PRINTS the distance

EVERY NUMBER HERE IS A GUESS, labelled with what would falsify it, the
same discipline as weighting.py and velocity.py. There is no
interaction data to tune against and no revenue yet.
"""
from __future__ import annotations

from typing import Optional

from src.core.base_model import utcnow

#: How many cards one supplier may hold on a rail, by plan.
#:
#: THE PRICING LEVER, and the only ceiling a plan can move. The
#: proportional ceiling in algorithms/interleave.py (40% of any rail)
#: binds underneath it and no tier passes that -- so on a 12-card rail
#: a MAX supplier's 5 is bound down to 4, and a rail is never fewer
#: than three distinct suppliers.
#:
#: THE STEPS ARE SMALL DELIBERATELY. A plan that doubled a supplier's
#: presence would be selling domination by instalments; one extra card
#: is a real advantage that still leaves the rail a market.
#:
#: FALSIFIED BY: suppliers finding the difference invisible, which
#: would mean the lever is too weak to sell -- or shops reporting the
#: same wholesaler everywhere, which would mean it is too strong.
ABSOLUTE_CAP_BY_TIER = {
    "FREE": 3,
    "PRO": 4,
    "MAX": 5,
    "PARTNER": 5,
}

#: The default when a tier is unknown or unreadable. FREE, always: a
#: bug in this module must cost a supplier reach rather than grant it.
DEFAULT_CAP = ABSOLUTE_CAP_BY_TIER["FREE"]

#: Rank order for breaking ties. Higher wins.
TIER_RANK = {"FREE": 0, "PRO": 1, "MAX": 2, "PARTNER": 2}

#: How close two suppliers must be before distance stops separating
#: them and tier is allowed to.
#:
#: 2km IS ABOUT THE SAME TRIP in township and peri-urban density -- the
#: same taxi, the same bakkie run, the same decision. Against
#: MAX_COLLECTION_KM = 25 it is 8% of the radius, so the proximity
#: promise visibly holds.
#:
#: ABSOLUTE, NOT PROPORTIONAL. "Within 25% of each other" was the
#: tempting alternative and fails at the top of the range: 20km and
#: 25km are within 25% and are not the same trip by any reading.
#:
#: NOT USED BY "COLLECT NEAR YOU" and that is not an oversight. That
#: rail prints the distance on every card, so any reordering is a
#: contradiction the reader is holding (V2_17 Q5). The band exists for
#: rails that rank on proximity WITHOUT showing it.
#:
#: FALSIFIED BY: shopkeepers treating 2km as a meaningful difference --
#: visible the day impressions exist, as a tap-rate gap between the
#: first and second card of a banded pair.
TOLERANCE_KM = 2.0


def effective_tier(profile) -> str:
    """The plan this supplier actually has RIGHT NOW.

    AN EXPIRED PLAN IS FREE, and this is the whole reason the function
    exists rather than reading the column. plan_expires_at is set for
    trials and PARTNER agreements; a lapsed plan that keeps its reach
    until some nightly job notices is reach nobody paid for, and the
    supplier who did pay is the one it is taken from.

    UNREADABLE MEANS FREE. A missing profile, a missing column, a value
    this module has never heard of -- all of them cost reach rather
    than grant it, because a bug here must fail towards the state
    nobody is billed for.
    """
    if profile is None:
        return "FREE"

    tier = getattr(profile, "plan_tier", None)
    name = getattr(tier, "value", tier)
    if name not in ABSOLUTE_CAP_BY_TIER:
        return "FREE"

    expires = getattr(profile, "plan_expires_at", None)
    if expires is not None and expires <= utcnow():
        return "FREE"

    return name


def absolute_cap(tier: Optional[str]) -> int:
    """How many cards this plan may hold on one rail, before the
    proportional ceiling has its say."""
    return ABSOLUTE_CAP_BY_TIER.get(tier or "FREE", DEFAULT_CAP)


def rank(tier: Optional[str]) -> int:
    """For ordering equals. Higher wins; unknown sorts last."""
    return TIER_RANK.get(tier or "FREE", 0)


def within_band(a_km: Optional[float], b_km: Optional[float]) -> bool:
    """Are these two close enough that distance no longer separates
    them?

    UNKNOWN IS NEVER TIED. If either distance is missing they are not
    equals, they are incomparable -- and treating incomparable as tied
    would let tier order things it was never given a fact about.
    """
    if a_km is None or b_km is None:
        return False
    return abs(a_km - b_km) <= TOLERANCE_KM
