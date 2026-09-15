"""
Keeping a rail a MARKET rather than one wholesaler's shelf.

TWO DIFFERENT PROTECTIONS, and they are routinely confused because both
sound like "don't let one supplier take over":

  THE CEILING   how many cards one supplier may hold at all.
  THE RUN       how many of them may sit next to each other.

A rail can honour the first and still fail the reader: four cards from
MacMan, then four from Lepelle, reads as two shopfronts stapled
together rather than a market. The eye sees the block before it counts
the cards.

WHY INTERLEAVING IS NOT SHUFFLING, which was the tempting shortcut.
The incoming order is not arbitrary -- it carries the demand engine's
weights, then affordability, then whatever offer_selection decided.
Randomising it throws away the reason the rail exists in order to solve
a layout problem. So this preserves the ranking and only breaks up
RUNS: the next card is the best remaining one whose supplier would not
form a streak.

EVERY NUMBER HERE IS A GUESS, labelled like the rest of the feed's
numbers (weighting.py, velocity.py). There is no interaction data to
tune against yet.
"""
from __future__ import annotations

from typing import Callable, List, Optional

#: How many cards from one supplier may sit consecutively.
#:
#: ONE, because the whole point is that the reader's eye never lands on
#: a block. Two would halve the interleaving for no stated benefit, and
#: the cost of one is only that a strongly-ranked supplier's second card
#: waits one position.
#:
#: FALSIFIED BY: rails where alternating visibly hurts relevance --
#: which impressions would show as a tap-rate drop between the first
#: card and the second.
MAX_CONSECUTIVE_PER_SUPPLIER = 1

#: The share of any rail one supplier may hold, whatever their plan.
#:
#: NO TIER MAY PASS THIS (V2_16, V2_17 Q3). The per-supplier ABSOLUTE
#: cap is the pricing lever -- it rises with plan -- and this is the
#: floor underneath it that money cannot move. On a 12-card rail it
#: allows 4, so a rail is never fewer than three distinct suppliers.
#:
#: IT BINDS HARDER ON SHORT RAILS, which is correct: 2 cards out of 5
#: from one supplier is already lopsided, and 40% says so.
#:
#: FALSIFIED BY: thin catalogues where honouring it empties rails. That
#: is a real risk on a young platform and is why the effective cap is
#: the SMALLER of the two ceilings rather than this one alone -- see
#: effective_cap.
PROPORTIONAL_CEILING = 0.4


def effective_cap(absolute_cap: int, rail_size: int) -> int:
    """How many cards one supplier may actually hold on this rail.

    THE SMALLER OF THE TWO CEILINGS WINS, and which one binds is the
    whole design: the absolute cap is what a plan buys (3 free, 5 max),
    and the proportional ceiling is the floor beneath it that no plan
    can lift. On a 12-card rail a MAX supplier's 5 is bound down to 4.

    NEVER RETURNS ZERO. A rail so short that 40% rounds to nothing
    would otherwise show nothing at all, which trades a lopsided rail
    for an empty one -- strictly worse, and not what the ceiling is for.
    """
    if rail_size <= 0:
        return max(1, absolute_cap)
    proportional = int(rail_size * PROPORTIONAL_CEILING)
    return max(1, min(absolute_cap, proportional))


def cap_per_supplier(
    cards: List[dict],
    cap: int,
    *,
    key: Callable[[dict], object] = lambda c: c.get("supplierId"),
) -> List[dict]:
    """Drop a supplier's cards past `cap`, preserving order.

    Moved here from sections.py, where it had lived since the first
    feed, so the ceiling and the run rule are read together -- they are
    two halves of one property and were a file apart.
    """
    seen: dict = {}
    kept: List[dict] = []
    for card in cards:
        owner = key(card)
        count = seen.get(owner, 0)
        if count >= cap:
            continue
        seen[owner] = count + 1
        kept.append(card)
    return kept


def break_up_runs(
    cards: List[dict],
    *,
    max_consecutive: int = MAX_CONSECUTIVE_PER_SUPPLIER,
    key: Callable[[dict], object] = lambda c: c.get("supplierId"),
) -> List[dict]:
    """Reorder so no supplier holds more than `max_consecutive` cards in
    a row, keeping the incoming ranking otherwise intact.

    GREEDY AND STABLE. At each step it takes the FIRST remaining card
    whose supplier would not form a run -- so a card only ever moves
    later, and only far enough to break the streak. A round-robin would
    have been simpler and would have thrown the ranking away.

    WHEN EVERY REMAINING CARD IS FROM THE SAME SUPPLIER it takes the
    next one anyway rather than dropping it. The run rule is a layout
    preference; the ceiling above is the real protection, and it has
    already run. Dropping stock to avoid two adjacent cards would be
    the layout tail wagging the catalogue dog.
    """
    remaining = list(cards)
    out: List[dict] = []

    while remaining:
        index = _first_without_run(remaining, out, max_consecutive, key)
        out.append(remaining.pop(index))

    return out


def _first_without_run(
    remaining: List[dict],
    placed: List[dict],
    max_consecutive: int,
    key: Callable[[dict], object],
) -> int:
    tail_owner, tail_len = _trailing_run(placed, key)

    for index, card in enumerate(remaining):
        if key(card) != tail_owner or tail_len < max_consecutive:
            return index

    # Everything left belongs to the supplier already at the tail.
    return 0


def _trailing_run(placed: List[dict], key: Callable[[dict], object]):
    """(supplier, how many of theirs end the list so far)."""
    if not placed:
        return None, 0
    owner = key(placed[-1])
    length = 0
    for card in reversed(placed):
        if key(card) != owner:
            break
        length += 1
    return owner, length


def arrange(
    cards: List[dict],
    *,
    absolute_cap: int,
    limit: Optional[int] = None,
    key: Callable[[dict], object] = lambda c: c.get("supplierId"),
) -> List[dict]:
    """Cap, then interleave, then trim. THE ORDER MATTERS.

    Capping BEFORE interleaving means the run rule arranges cards that
    have already earned their place. Interleaving first would spread a
    dominant supplier's cards evenly across the rail and THEN remove
    some, leaving gaps in a pattern that was built around them.

    Trimming LAST means `limit` counts cards the reader will actually
    see, so a rail asked for 12 returns 12 whenever 12 exist.
    """
    rail_size = limit if limit is not None else len(cards)
    kept = cap_per_supplier(cards, effective_cap(absolute_cap, rail_size), key=key)
    arranged = break_up_runs(kept, key=key)
    return arranged[:limit] if limit else arranged
