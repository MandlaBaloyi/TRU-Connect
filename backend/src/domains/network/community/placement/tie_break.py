"""
Ordering the equals.

THE SENTENCE THIS FILE IMPLEMENTS:

    A rail may be tie-broken only if it does not DISPLAY the fact it is
    ordered by.

That test, applied honestly, gives opposite answers for the two
proximity rails and the difference is not a matter of taste:

    COLLECT NEAR YOU        prints "1.2 km" on every card. Reordering
                            it puts 2.0km above 1.2km in front of a
                            reader who can see both numbers. They
                            conclude either that the app is broken or
                            that the order was bought -- and the second
                            conclusion is the correct one, which is
                            what makes it unrecoverable. NOT SELLABLE.

    SUPPLIERS YOU HAVEN'T   prints no number and no score. Its order
    ORDERED FROM            is not a claim the reader can check, so
                            ordering equals by tier costs them nothing
                            they can detect and nothing they were
                            promised. SELLABLE.

THE ORGANIC FACT ALWAYS RANKS FIRST. Tier enters the sort key after it,
never inside it. That is the whole mechanical difference between a
tie-break and an auction.
"""
from __future__ import annotations

from typing import Callable, List, Optional

from src.domains.network.community.placement import tier_rules


def order_untried_suppliers(
    profiles: List,
    *,
    connected_ids: set,
    relevance: Optional[dict] = None,
    tier_of: Optional[Callable[[object], str]] = None,
) -> List:
    """Suppliers this shop has never ordered from, best first.

    THE FACT: do they already know them? A connected supplier is the
    cheapest first order on the rail -- the trust is done and only the
    order is missing -- so that separates the list before anything else
    is considered, at every tier, for any money.

    THEN RELEVANCE, AND IT IS ALSO A FACT. This paragraph used to say
    "two strangers who both stock what this shop buys are genuinely
    indistinguishable from the shop's own data" -- which quietly
    assumed somebody had checked whether they stocked it. Nobody had.
    The rail took every visible supplier with stock and let the
    alphabet decide, so a nappy distributor could sit above the
    wholesaler carrying everything this shop actually buys.

    RELEVANCE SORTS ABOVE TIER because of this file's own rule: the
    organic fact ranks first, and what a shop buys is a fact about the
    shop that nobody bought and no supplier can change. A paying
    supplier therefore cannot outrank one that sells what this shop
    needs -- money still breaks ties, it just breaks them lower down.

    THE TIE-BREAK: within each group, plan orders the equals. NOW the
    sentence above is true -- two strangers who both stock what this
    shop buys really are indistinguishable from the shop's own data,
    because relevance has already separated everyone for whom that is
    false.

    NO RELEVANCE MAP MEANS NO OPINION, not a score of zero for
    everybody. A shop that has declared nothing and ordered nothing
    gets exactly the old ordering, which is the correct answer for the
    user this rail exists for.

    THE ALPHABET STILL BREAKS THE LAST TIE, so the order is
    deterministic. A rail that reorders between identical requests is
    one nobody can debug.
    """
    resolve = tier_of or tier_rules.effective_tier
    scores = relevance or {}

    return sorted(
        profiles,
        key=lambda p: (
            # 1. THE FACT -- False (known) sorts before True (stranger).
            str(p.id) not in connected_ids,
            # 2. THE OTHER FACT -- negated so a better match comes
            #    first. ABOVE tier, deliberately: see the docstring.
            -scores.get(p.id, 0.0),
            # 3. THE TIE-BREAK -- negated so higher rank comes first.
            -tier_rules.rank(resolve(p)),
            # 4. DETERMINISM.
            (p.business_name or "").lower(),
        ),
    )
