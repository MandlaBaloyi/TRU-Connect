"""
CONSIDERED signals: what the shop was shown and did not buy.

THE THIRD KIND OF EVIDENCE, and the weakest of the three on purpose:

    DECLARED    what they said, filling in a form.   A hypothesis.
    OBSERVED    what they bought.                    Proof.
    CONSIDERED  what the feed put in front of them.  A hint.

A card delivered is not an intention. It is not even attention -- see
feed_impression.py on why the column is called "delivered" rather than
"shown": a card below the fold was sent and never looked at. What this
module can honestly say is "bakery has been on this shop's screen
forty times this month and they have never bought any", and that is
worth something precisely because the declared and observed signals are
both silent on it.

WHY IT EXISTS AT ALL. The gap it fills is the shop that declared
nothing and has bought little -- the first three weeks of every
account, which is exactly when the feed is least able to help and most
needs to. Declared is empty because nobody filled in the form; observed
is empty because there is no history. The feed has still been showing
them things, and what they ignored is information.

───────────────────────────────────────────────────────────────────────
HOW THIS STAYS INSIDE THE SUPPLIER-BLIND WALL

The impressions table has a supplier_profile_id on it, because
sponsored billing requires one. The demand engine may not know who a
supplier is -- tests/architecture/test_demand_independence.py parses
the imports of this whole package and fails the build on
src.domains.supplier, src.domains.network.connections or
src.domains.verification.

That test checks IMPORTS, not COLUMNS, so "may read the table but must
not select that column" would be a rule enforced by nobody. The answer
is that this module never queries the table. It calls ONE repository
method which returns Dict[str, int] -- a category and a count. There is
no field in that shape for a supplier to hide in, so leaking one would
require changing a signature, which is a visible act rather than an
accident on a busy week.

THE INVARIANT, RESTATED: the model describes the SHOP. What this shop
has been shown and ignored is a fact about the shop. What must never
appear is who was offering it, and it cannot.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict
from uuid import UUID

from src.core.base_model import utcnow

#: HOW FAR BACK TO LOOK. A month, because the question is "has this
#: shop been ignoring bakery lately" rather than "ever" -- a category
#: they stopped buying in March should not still be counted against
#: them in September.
#:
#: FALSIFIER, in the same shape as the rest of the engine's numbers: if
#: the considered signal keeps naming categories a shop DID buy within
#: the window, the window is too long and the observed signal is
#: arriving after this one has already spoken.
CONSIDERED_WINDOW_DAYS = 30

#: BELOW THIS, SILENCE. One card delivered is noise -- it means the
#: feed had a slot to fill, not that the shop saw anything. A category
#: has to have been put in front of them repeatedly before their not
#: buying it means anything at all.
MIN_DELIVERED_TO_COUNT = 5


@dataclass(frozen=True)
class ConsideredSignals:
    """What the feed showed, with nothing inferred yet.

    NO SUPPLIER FIELD, NOW OR EVER. This dataclass is the shape the
    rest of the engine sees, and its absence of a supplier is the
    second half of the guarantee the repository's return type makes --
    stated here too because the two files will be read separately.
    """

    #: {category: cards delivered in the window}. Raw counts, not
    #: weights -- the same rule ObservedSignals follows, and for the
    #: same reason: a signal that pre-scores itself scatters the
    #: weighting across six files.
    category_delivered: Dict[str, int] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.category_delivered


def considered_for(business_id: UUID) -> ConsideredSignals:
    """What this shop has been shown lately.

    ONE CALL, ONE NARROW SHAPE. See the module docstring: this is the
    only route from the demand engine to the impressions table, and it
    is narrow by construction rather than by discipline.
    """
    from src.domains.network.impressions.repositories.impression_repository import (
        ImpressionRepository,
    )

    since = (utcnow() - timedelta(days=CONSIDERED_WINDOW_DAYS)).date()
    delivered = ImpressionRepository.categories_considered(business_id, since=since)

    return ConsideredSignals(
        category_delivered={
            category: count
            for category, count in delivered.items()
            if count >= MIN_DELIVERED_TO_COUNT
        }
    )
