"""
Does this supplier sell what this shop buys?

THE HOLE THIS FILLS. Both discovery rails recommended suppliers without
ever asking what the shop needs. not_ordered_yet_suppliers took every
visible supplier with stock and sorted them alphabetically;
collect_near_you sorted by distance and nothing else. The demand engine
has known the answer since V2_15 and neither rail consulted it.

It was invisible on a seeded catalogue of broad wholesalers who each
carry a bit of everything. In a real market of specialists it is the
obvious failure: a nappy distributor recommended to a hair salon,
forever, because the alphabet put them third.

tie_break's own docstring had already assumed this was handled --
"two strangers who both stock what this shop buys are genuinely
indistinguishable from the shop's own data". They were not both
stocking it. Nothing had checked.

───────────────────────────────────────────────────────────────────────
WHY THE SCORE LIVES HERE AND NOT IN THE DEMAND ENGINE

The engine is SUPPLIER-BLIND, enforced by
tests/architecture/test_demand_independence.py: it answers "what does
this shop need" and the answer may never contain a supplier. Matching a
supplier against that answer is therefore not its work.

community/ may see both sides -- it is the composer -- so the join
belongs here, with the other placement rules. The engine hands over
weights; this file decides who matches them.

───────────────────────────────────────────────────────────────────────
RELEVANCE IS AN ORGANIC FACT, WHICH DECIDES WHERE IT SORTS

tie_break states the rule that matters:

    THE ORGANIC FACT ALWAYS RANKS FIRST. Tier enters the sort key after
    it, never inside it. That is the whole mechanical difference
    between a tie-break and an auction.

What a shop buys is a fact about the shop. Nobody bought it, and no
supplier can change it. So relevance sorts ABOVE tier -- which means a
paying supplier can never outrank one that actually sells what this
shop needs. That strengthens the anti-domination property rather than
bending it: money still breaks ties, and now it breaks them lower down.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set

from src.extensions import db


def categories_by_supplier(profile_ids: Iterable) -> Dict:
    """{supplier_profile_id: {category, ...}} for live offers.

    ONE QUERY FOR THE WHOLE CANDIDATE SET. The obvious implementation
    asks per supplier inside the ranking loop, which is the N+1 this
    package has now removed three times -- most recently one image
    query per card, in a file whose own docstring claimed it batched
    everything.

    LIVE OFFERS ONLY. An archived or deleted listing is not something
    the shop could buy, so counting it would recommend a supplier for
    stock they have withdrawn.
    """
    ids = [pid for pid in profile_ids if pid]
    if not ids:
        return {}

    from src.domains.supplier.products.models.supplier_offer import SupplierOffer

    rows = (
        db.session.query(SupplierOffer.supplier_profile_id, SupplierOffer.category)
        .filter(
            SupplierOffer.supplier_profile_id.in_(ids),
            SupplierOffer.is_deleted.is_(False),
            SupplierOffer.is_archived.is_(False),
        )
        .distinct()
        .all()
    )

    found: Dict = {}
    for supplier_id, category in rows:
        value = getattr(category, "value", category)
        if value:
            found.setdefault(supplier_id, set()).add(value)
    return found


def score(carried: Optional[Set[str]], weights: Dict[str, float]) -> float:
    """How well this supplier matches what the shop buys.

    THE SUM OF THE SHOP'S OWN WEIGHTS for the categories this supplier
    actually carries. A shop that buys mostly bakery and a little
    beverages scores a bakery wholesaler above a drinks distributor,
    and both above somebody selling neither -- using the same weights
    "Stock for your shop" already ranks products with, so the two
    surfaces cannot disagree about what this shop needs.

    NOT NORMALISED BY CATALOGUE SIZE, deliberately. Dividing by how
    many categories a supplier carries would penalise a cash-and-carry
    for being a cash-and-carry; carrying everything the shop buys IS
    the most useful thing a supplier can do for it. The anti-domination
    rule is about one supplier owning a RAIL of products, which
    interleave.arrange still enforces separately.

    ZERO IS A REAL ANSWER and the caller decides what it means. On the
    untried rail it sorts last; on collect-near-you it is the filter.
    """
    if not carried or not weights:
        return 0.0
    return sum(weight for category, weight in weights.items() if category in carried)


def sells_anything_needed(carried: Optional[Set[str]], wanted: Set[str]) -> bool:
    """A yes/no for the filter, separate from the score on purpose.

    "SCORES ZERO" AND "SELLS NOTHING THEY BUY" ARE NOT THE SAME
    QUESTION, even though today they coincide. A weight could become
    zero for a category a shop has stopped buying without that meaning
    the supplier is irrelevant, and a filter built on the score would
    then hide somebody for the wrong reason. Asking membership
    directly keeps the filter honest if weighting ever changes.
    """
    if not wanted:
        # NO DECLARED NEEDS MEANS NO OPINION, never "matches nothing".
        # This is the day-one shop, and it is the one the discovery
        # rails exist for.
        return True
    return bool(carried and (carried & wanted))


def rank(profiles: List, *, weights: Dict[str, float]) -> Dict:
    """{profile_id: score} for a set of candidates, in one query."""
    carried = categories_by_supplier([p.id for p in profiles])
    return {p.id: score(carried.get(p.id), weights) for p in profiles}
