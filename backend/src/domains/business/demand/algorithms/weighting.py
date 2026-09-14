"""
Turning signals into weights and confidence.

EVERY NUMBER IN THIS FILE IS A GUESS, and saying so is the point. There
is no interaction data to tune against yet, so these are starting
positions chosen to be defensible rather than optimal -- and each one
carries what would prove it wrong. A number nobody chose becomes
permanent precisely because nobody remembers it was arbitrary.

NOTHING HERE TOUCHES A DATABASE. Plain values in, plain values out, so
the reasoning can be tested without a fixture and read without context.
"""
from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

#: A shop ticking a category is real evidence and weaker than buying
#: from it forty times. Half is the honest middle: enough to act on,
#: never enough to outrank behaviour once behaviour exists.
#:
#: FALSIFIED BY: declared categories that observation contradicts more
#: often than it confirms. If most shops buy outside what they declared,
#: this is too high.
DECLARED_CONFIDENCE = 0.5

#: Everything known about a shop that has answered nothing. Not zero --
#: a shop with no profile still gets the platform-wide fallback feed,
#: and zero would imply we know it is wrong rather than absent.
UNKNOWN_CONFIDENCE = 0.0

#: Answering the two quick questions is worth real confidence, because
#: cadence and budget are what make a recommendation TIMELY rather than
#: merely relevant.
RHYTHM_CONFIDENCE_BONUS = 0.15
SPEND_CONFIDENCE_BONUS = 0.15


# ---------------------------------------------------------------------------
# Cadence
# ---------------------------------------------------------------------------

#: Declared rhythm, as days between restocks. Used until real order
#: history produces a measured gap, which always wins.
#:
#: IRREGULAR IS DELIBERATELY None, not a large number. "They buy when
#: they run out" is a real answer and inventing 30 days for it would
#: make the feed confidently wrong about timing -- the one kind of wrong
#: that sends somebody a nudge on the wrong day.
RHYTHM_DAYS = {
    "DAILY": 1.0,
    "TWICE_WEEKLY": 3.5,
    "WEEKLY": 7.0,
    "FORTNIGHTLY": 14.0,
    "MONTHLY": 30.0,
    "IRREGULAR": None,
}


# ---------------------------------------------------------------------------
# Basket
# ---------------------------------------------------------------------------

#: The top of a plausible single order, in cents, per weekly spend band.
#:
#: A WEEK'S BUDGET IS NOT ONE ORDER'S BUDGET, which is why these are not
#: simply the band's upper bound: a shop spending R2,000 a week across
#: two or three deliveries is not buying a R2,000 pallet. The multiplier
#: is deliberately generous -- the cost of being slightly too high is a
#: card they scroll past, and of being too low is hiding something they
#: would have bought.
SPEND_BAND_ORDER_CEILING_CENTS = {
    "UNDER_500": 50_000,
    "R500_TO_2000": 150_000,
    "R2000_TO_5000": 400_000,
    "R5000_TO_10000": 800_000,
    "OVER_10000": None,  # no ceiling worth applying
}

#: Shops serving other businesses buy cases; shops serving walk-ins buy
#: singles and small packs. The only pack-size signal available before a
#: first order.
WHOLESALE_CUSTOMER_TYPES = {"OTHER_BUSINESSES", "ORGANISATIONS"}

#: How far above a shop's TYPICAL basket a single product may be priced
#: and still belong at the front of their feed.
#:
#: A shop whose median order is R600 can plausibly stretch to a R900
#: item -- one big bag of maize IS the order that week. It cannot
#: plausibly buy a R9,000 pallet, and a feed that leads with one has
#: mistaken this shop for a different business.
#:
#: DELIBERATELY GENEROUS, because this orders a rail rather than
#: censoring it (see browse_service): the cost of being too high is a
#: card they scroll past, and of being too low is burying something they
#: would have bought.
#:
#: FALSIFIED BY: real order lines landing above this multiple often. If
#: shops routinely buy single items worth more than 1.5 baskets, the
#: median basket is the wrong denominator, not the multiplier.
AFFORDABLE_LINE_MULTIPLE = 1.5


def declared_category_weight(_category: str) -> float:
    """Every declared category starts equal.

    RANKING THEM WOULD BE INVENTING AN ORDER THE SHOP NEVER GAVE. A form
    with chips has no first choice -- the order on screen is
    alphabetical, and treating the top chip as more important would turn
    a layout accident into a recommendation. Observation is what
    separates them later.
    """
    return 1.0


def overall_confidence(
    *, has_categories: bool, has_rhythm: bool, has_spend: bool
) -> float:
    """How much the feed should lean on this model versus falling back
    to platform-wide defaults."""
    if not has_categories:
        return UNKNOWN_CONFIDENCE

    score = DECLARED_CONFIDENCE
    if has_rhythm:
        score += RHYTHM_CONFIDENCE_BONUS
    if has_spend:
        score += SPEND_CONFIDENCE_BONUS
    return min(1.0, round(score, 3))


def cadence_days(rhythm: Optional[str]) -> Optional[float]:
    if not rhythm:
        return None
    return RHYTHM_DAYS.get(rhythm)


def order_ceiling_cents(spend_band: Optional[str]) -> Optional[int]:
    if not spend_band:
        return None
    return SPEND_BAND_ORDER_CEILING_CENTS.get(spend_band)


def prefers_bulk(customer_types) -> Optional[bool]:
    """None means UNKNOWN, never "no".

    A shop that has not said who its customers are has not said it sells
    to walk-ins, and defaulting a tri-state to one of its answers is the
    mistake offers_delivery already records having made once.
    """
    if not customer_types:
        return None
    return any(t in WHOLESALE_CUSTOMER_TYPES for t in customer_types)


def max_line_cents(
    typical_order_cents: Optional[int],
    declared_ceiling_cents: Optional[int],
) -> Optional[int]:
    """The most one product can cost and still lead this shop's feed.

    MEASURED BEATS DECLARED, the same rule cadence follows: a median of
    real baskets says more about what this shop can spend than the band
    they picked off a form once.

    None means UNKNOWN, and every caller must treat it as "do not
    filter" rather than inventing a ceiling. Most shops have neither
    signal on day one, and a number that looks real is worse than an
    absent one (flaw B.5).
    """
    if typical_order_cents:
        return int(typical_order_cents * AFFORDABLE_LINE_MULTIPLE)
    return declared_ceiling_cents
