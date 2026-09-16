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

PHASE 1: DECLARED AND OBSERVED. Order history is read now and
reconciled against what the shop said (reconciliation.py). The public
shape did not change when that landed, which was the point of keeping
this module the only thing the feed may call.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.domains.business.demand.algorithms import weighting
from src.domains.business.demand.services import reconciliation
from src.domains.business.demand.signals import declared as declared_signals
from src.domains.business.demand.signals import observed as observed_signals


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
    #: Categories this shop SAYS it buys and has never bought here.
    #: A confirmed need we are losing to somebody else -- worth more to
    #: us than to the feed. See reconciliation.unserved_categories.
    unserved: List[str] = field(default_factory=list)
    #: Typical basket, measured. None until they have ordered.
    typical_order_cents: Optional[int] = None
    #: True = has transport, False = needs delivery, None = has not
    #: said. None IS NOT False, and the feed must not treat it as such
    #: -- an unanswered question is an absence, not an answer, and the
    #: whole reason the column is nullable is so a guess cannot be
    #: mistaken for a fact later.
    can_collect: Optional[bool] = None

    @property
    def is_known(self) -> bool:
        return bool(self.categories)

    @property
    def category_values(self) -> List[str]:
        return [c.category for c in self.categories]

    @property
    def max_line_cents(self) -> Optional[int]:
        """The most one product can cost and still lead this shop's feed.

        A QUESTION THE ENGINE ANSWERS, not a sum the feed does. The
        moment a feed source multiplies a basket by a constant of its
        own, the constant is in two places and one of them will be
        forgotten -- which is the entire reason weighting.py exists.
        """
        return weighting.max_line_cents(
            self.typical_order_cents, self.order_ceiling_cents
        )

    @property
    def weight_by_category(self) -> dict:
        """{category: weight}, for ordering a rail by what matters most
        to THIS shop rather than by whatever order the catalogue
        returned. Cheap, and it saves every caller rebuilding it."""
        return {c.category: c.weight for c in self.categories}


def needs_for(business_id) -> ShopNeeds:
    """What this shop needs, as far as we can tell today.

    NEVER RAISES AND NEVER RETURNS None. A shop that has told us nothing
    gets an empty ShopNeeds with zero confidence, and every caller can
    treat that as "fall back to something platform-wide" without a
    special case. An engine that throws on an unfilled form would make
    the feed depend on the form, which is exactly backwards.
    """
    said = declared_signals.read(business_id)
    did = observed_signals.read(business_id)

    merged = reconciliation.merge(said.categories, did.category_counts)

    categories = [
        CategoryNeed(
            category=n["category"],
            weight=n["weight"],
            confidence=n["confidence"],
            source=n["source"],
        )
        for n in merged
    ]

    # MEASURED BEATS DECLARED, every time. A shop that SAID weekly and
    # actually orders every four days is telling us two things, and only
    # one of them is a memory of how they think their shop runs.
    cadence = did.measured_gap_days or weighting.cadence_days(said.restock_rhythm)

    return ShopNeeds(
        categories=categories,
        cadence_days=cadence,
        order_ceiling_cents=weighting.order_ceiling_cents(said.weekly_spend_band),
        prefers_bulk=weighting.prefers_bulk(said.customer_types),
        confidence=weighting.overall_confidence(
            has_categories=bool(categories),
            has_rhythm=bool(said.restock_rhythm) or did.measured_gap_days is not None,
            has_spend=bool(said.weekly_spend_band) or did.typical_order_cents is not None,
        ),
        unserved=reconciliation.unserved_categories(merged),
        typical_order_cents=did.typical_order_cents,
        # DECLARED ONLY, and deliberately not "measured" from order
        # history. A shop with no collection orders might have no
        # transport, or might simply have bought from suppliers who
        # deliver -- those are indistinguishable from here, and
        # inferring the first would be exactly the invented answer this
        # field exists to avoid.
        can_collect=said.can_collect,
    )
