"""
THE PUBLIC FACE OF THE DEMAND ENGINE.

One question: WHAT DOES THIS SHOP NEED?

This is the only module the feed is allowed to call. Everything else
under demand/ is how the answer is built, and keeping that private is
what lets the model change -- gain an observed layer, gain a nightly
rebuild, gain a learned weight -- without a single feed source noticing.

THE ANSWER NEVER NAMES A SUPPLIER. It names CATEGORIES, a cadence, a
budget and a confidence. Who can fulfil any of it is a separate
question, asked afterwards, by somebody else (catalogue/discovery).

PHASE 0 IS DECLARED-ONLY. Order history is not read yet -- that is
Phase 1 -- and the shape below is deliberately the shape it will keep,
so adding observation changes the numbers and not the callers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.domains.business.demand.algorithms import weighting
from src.domains.business.demand.signals import declared as declared_signals


@dataclass(frozen=True)
class CategoryNeed:
    """One thing this shop buys, and how sure we are."""

    category: str
    weight: float
    confidence: float
    #: "declared" | "observed" | "both" -- the PROVENANCE, and it is not
    #: decoration: a feed that cannot say "we think you buy bread
    #: because you told us" versus "because you have bought it nine
    #: times" cannot explain itself, and an unexplainable feed is one
    #: nobody dares change.
    source: str


@dataclass(frozen=True)
class ShopNeeds:
    categories: List[CategoryNeed] = field(default_factory=list)
    #: Days between restocks. None when unknown OR when the shop said
    #: "when I run out" -- inventing a number there would make the feed
    #: confidently wrong about timing.
    cadence_days: Optional[float] = None
    #: The top of a plausible single order. None means do not filter.
    order_ceiling_cents: Optional[int] = None
    #: True = buys cases, False = buys singles, None = has not said.
    prefers_bulk: Optional[bool] = None
    #: How far the feed should lean on this rather than platform-wide
    #: defaults. 0.0 means "we know nothing", which is a real state.
    confidence: float = 0.0

    @property
    def is_known(self) -> bool:
        return bool(self.categories)

    @property
    def category_values(self) -> List[str]:
        return [c.category for c in self.categories]


def needs_for(business_id) -> ShopNeeds:
    """What this shop needs, as far as we can tell today.

    NEVER RAISES AND NEVER RETURNS None. A shop that has told us nothing
    gets an empty ShopNeeds with zero confidence, and every caller can
    treat that as "fall back to something platform-wide" without a
    special case. An engine that throws on an unfilled form would make
    the feed depend on the form, which is exactly backwards.
    """
    signals = declared_signals.read(business_id)

    categories = [
        CategoryNeed(
            category=value,
            weight=weighting.declared_category_weight(value),
            confidence=weighting.DECLARED_CONFIDENCE,
            source="declared",
        )
        for value in signals.categories
    ]

    return ShopNeeds(
        categories=categories,
        cadence_days=weighting.cadence_days(signals.restock_rhythm),
        order_ceiling_cents=weighting.order_ceiling_cents(signals.weekly_spend_band),
        prefers_bulk=weighting.prefers_bulk(signals.customer_types),
        confidence=weighting.overall_confidence(
            has_categories=bool(signals.categories),
            has_rhythm=bool(signals.restock_rhythm),
            has_spend=bool(signals.weekly_spend_band),
        ),
    )
