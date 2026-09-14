"""
What is moving fast right now.

THE DIFFERENCE BETWEEN THIS AND A BESTSELLER LIST, and it is the whole
design: a bestseller list is a product that has always sold well, which
a shopkeeper already knows about and does not need a rail to discover.
"Moving fast" is a product selling faster THAN ITSELF -- a change, not a
level. Maize meal before a long weekend, cooldrink in a heatwave, school
stationery in January.

SO EVERY PRODUCT IS COMPARED TO ITS OWN PAST, never to other products.
Comparing across products would rank a wholesaler's case of 24 above a
single loaf forever, and the rail would silently become a list of things
that come in big boxes.

EVERY NUMBER HERE IS A GUESS, same discipline as the demand engine's
weighting.py: there is no interaction data to tune against yet, so these
are defensible starting positions and each one carries what would prove
it wrong. A number nobody chose becomes permanent precisely because
nobody remembers it was arbitrary.
"""
from __future__ import annotations

from typing import Dict, List, Optional

#: The window that counts as "right now".
#:
#: SEVEN DAYS BECAUSE A SHOP'S WEEK IS THE REAL UNIT. Informal trade
#: runs on a weekly rhythm -- payday, weekend, month-end -- and a
#: shorter window would turn one busy Saturday into a platform-wide
#: trend. Longer, and a rail called "right now" stops being true.
#:
#: FALSIFIED BY: spikes that are over before the rail notices them. If
#: the things surfacing here are consistently stale by the time a shop
#: sees them, this is too long.
RECENT_DAYS = 7

#: What the recent window is measured against: the four weeks before it.
#:
#: FOUR WEEKS, NOT ONE, so the baseline is a normal month rather than
#: whatever last week happened to be. Comparing a week to a week makes
#: every product that had a quiet week look like it is surging.
#:
#: FALSIFIED BY: seasonal products reading as spikes every time their
#: season starts. That is arguably correct -- it IS moving fast -- but
#: if the rail fills with the same products every December, the baseline
#: needs to be last year, not last month.
BASELINE_DAYS = 28

#: How much faster than its own baseline a product must be moving.
#:
#: 1.5x IS DELIBERATELY MODEST. The rail is filtered to categories this
#: shop already buys, so its candidates are few; a dramatic threshold
#: would leave it empty on a platform this size, and an empty rail
#: teaches people the tab is broken.
#:
#: FALSIFIED BY: the rail filling with noise. If shops scroll past it,
#: this is too low -- and that is exactly the judgement impressions
#: would settle, which is why this number is a guess and not a finding.
SPIKE_RATIO = 1.5

#: Units in the recent window before a product can qualify at all.
#:
#: THE PROTECTION AGAINST TINY NUMBERS. Without it, one unit last week
#: against zero the month before is an infinite increase, and the rail
#: fills with things exactly one person bought once. This is a
#: STATISTICAL floor, not a privacy one -- the count shown to anybody is
#: the buyer count in social_proof.py, which Mandla decided needs no
#: minimum.
#:
#: FALSIFIED BY: a catalogue where genuine movement never reaches three
#: units a week. On a platform this young that is plausible, and this
#: is the first number to lower.
MIN_RECENT_UNITS = 3


def rising_products(
    recent_units: Dict,
    baseline_units: Dict,
    *,
    limit: Optional[int] = None,
) -> List:
    """Product ids moving faster than their own recent past, strongest
    first.

    TAKES TWO PLAIN MAPS, touches no database. The repository fetches
    both windows; the judgement lives here where it can be read and
    tested without a fixture -- the same split weighting.py uses.

    A PRODUCT WITH NO BASELINE IS NEW, NOT INFINITE. Dividing by zero
    would rank every brand-new product above everything real. It is
    instead compared against the minimum units threshold, so a genuinely
    busy new product can still qualify while a single first sale cannot.
    """
    scored = []

    for product_id, recent in recent_units.items():
        if recent < MIN_RECENT_UNITS:
            continue

        # Per-day rates, because the two windows are different lengths.
        # Comparing 7 days of units against 28 days of units directly
        # would make almost nothing look like it was rising.
        recent_rate = recent / RECENT_DAYS
        baseline = baseline_units.get(product_id, 0)
        baseline_rate = baseline / BASELINE_DAYS if baseline else 0.0

        if baseline_rate == 0:
            # NEW OR NEWLY STOCKED. It already cleared MIN_RECENT_UNITS,
            # so this is real movement with nothing to compare against.
            ratio = float(SPIKE_RATIO)
        else:
            ratio = recent_rate / baseline_rate
            if ratio < SPIKE_RATIO:
                continue

        scored.append((ratio, recent, product_id))

    # Sharpest rise first; units break a tie so a big mover outranks a
    # small one at the same ratio; the id makes it deterministic, because
    # a rail that reorders between identical requests cannot be debugged.
    scored.sort(key=lambda row: (-row[0], -row[1], str(row[2])))

    ordered = [product_id for _, _, product_id in scored]
    return ordered[:limit] if limit else ordered
