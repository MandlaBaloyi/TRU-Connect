"""
When what a shop SAID and what a shop DID disagree.

THE RULE, AND IT IS A PRODUCT DECISION BEFORE IT IS A TECHNICAL ONE
(docs/v2/V2_15 Book Three Part 6):

    A shop declares bread. Six months of orders contain no bread.

    THE WRONG READING: they lied, drop the signal.
    THE RIGHT READING: THEY BUY BREAD SOMEWHERE ELSE.

That is not a data-quality problem. It is the single most valuable
thing this engine can learn, because it names a category where
TruConnect is losing a need the shop has already CONFIRMED it has --
and a confirmed unmet need is what makes a supplier conversation
concrete rather than speculative.

So a contradicted declaration is never silently dropped. It stays, with
its confidence intact and flagged UNSERVED.

THE THREE CASES:

    observed CONFIRMS declared      confidence rises, fast. Somebody
                                    told us and then proved it.
    observed CONTRADICTS declared   the declared weight STAYS, marked
                                    unserved. Never deleted.
    observed EXCEEDS declared       add the category at observed
                                    strength. They buy things they did
                                    not think to mention, which is
                                    normal -- a form is not an
                                    inventory.

DECLARED DECAYS, IT DOES NOT EXPIRE. A form filled fourteen months ago
is weaker evidence than one filled last week, but a shop that still
sells what it said it sells is the ordinary case. Decay the confidence,
keep the signal. (The decay itself waits for Phase 1's nightly rebuild
to have a timestamp to decay against.)
"""
from __future__ import annotations

from typing import Dict, List

from src.domains.business.demand.algorithms import weighting

#: Order lines in a category before observation is worth trusting on its
#: own. One line is an experiment; three is a habit.
#:
#: FALSIFIED BY: shops whose third purchase in a category is still their
#: last. If that is common, this is too low.
MIN_LINES_FOR_CONFIDENCE = 3


def merge(
    declared_categories: List[str],
    observed_counts: Dict[str, int],
) -> List[dict]:
    """Declared plus observed, as one ranked list of needs.

    Returns plain dicts rather than CategoryNeed objects so this stays
    testable without importing the service that shapes them -- the rule
    is the valuable part and it deserves to be readable on its own.
    """
    total_lines = sum(observed_counts.values()) or 1
    declared = set(declared_categories)
    observed = set(observed_counts)

    needs: List[dict] = []

    for category in declared | observed:
        lines = observed_counts.get(category, 0)
        share = lines / total_lines

        if category in declared and lines > 0:
            # CONFIRMED. Said and proved.
            needs.append(
                {
                    "category": category,
                    "weight": 1.0,
                    "confidence": _confirmed_confidence(lines),
                    "source": "both",
                    "unserved": False,
                }
            )
        elif category in declared:
            # CONTRADICTED -- or simply not yet bought here. Same shape
            # either way, because we cannot tell the difference and the
            # honest reading is the generous one.
            needs.append(
                {
                    "category": category,
                    "weight": 1.0,
                    "confidence": weighting.DECLARED_CONFIDENCE,
                    "source": "declared",
                    # THE FLAG THAT IS WORTH MORE THAN THE FEED. A
                    # category a shop says it buys and has never bought
                    # HERE is a need we are losing to somebody else.
                    "unserved": True,
                }
            )
        else:
            # EXCEEDS. They buy things they did not think to mention --
            # a form is not an inventory, and behaviour outranks it.
            needs.append(
                {
                    "category": category,
                    # Weighted by how much of their buying it is, so a
                    # category bought once does not sit level with the
                    # one they restock weekly.
                    "weight": round(min(1.0, 0.4 + share), 3),
                    "confidence": _confirmed_confidence(lines),
                    "source": "observed",
                    "unserved": False,
                }
            )

    # Strongest first, and DETERMINISTIC on ties: a feed whose order
    # changes between identical requests is one nobody can debug.
    needs.sort(key=lambda n: (-n["weight"], -n["confidence"], n["category"]))
    return needs


def _confirmed_confidence(lines: int) -> float:
    """How much evidence is in N order lines.

    RISES WITH REPETITION AND CAPS SHORT OF CERTAINTY. Forty purchases
    is strong evidence of a habit and still not proof of next month --
    shops change, and a model that reaches 1.0 has stopped being able to
    learn that.
    """
    if lines <= 0:
        return weighting.DECLARED_CONFIDENCE
    if lines < MIN_LINES_FOR_CONFIDENCE:
        return 0.7
    return min(0.95, 0.75 + 0.02 * lines)


def unserved_categories(needs: List[dict]) -> List[str]:
    """Categories this shop says it buys and has never bought here.

    READ BY US, NOT ONLY BY THE FEED. Aggregated across shops this is a
    product gap, a supplier acquisition target, and the most persuasive
    number available in a wholesaler conversation -- "412 shops near you
    buy airtime and cannot buy it here".
    """
    return [n["category"] for n in needs if n.get("unserved")]
