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
    tier_of: Optional[Callable[[object], str]] = None,
) -> List:
    """Suppliers this shop has never ordered from, best first.

    THE FACT: do they already know them? A connected supplier is the
    cheapest first order on the rail -- the trust is done and only the
    order is missing -- so that separates the list before anything else
    is considered, at every tier, for any money.

    THE TIE-BREAK: within each group, plan orders the equals. Two
    strangers who both stock what this shop buys are genuinely
    indistinguishable from the shop's own data; the alphabet was
    breaking that tie before, which is not a fairer rule, just a
    blinder one.

    THE ALPHABET STILL BREAKS THE LAST TIE, so the order is
    deterministic. A rail that reorders between identical requests is
    one nobody can debug.
    """
    resolve = tier_of or tier_rules.effective_tier

    return sorted(
        profiles,
        key=lambda p: (
            # 1. THE FACT -- False (known) sorts before True (stranger).
            str(p.id) not in connected_ids,
            # 2. THE TIE-BREAK -- negated so higher rank comes first.
            -tier_rules.rank(resolve(p)),
            # 3. DETERMINISM.
            (p.business_name or "").lower(),
        ),
    )
