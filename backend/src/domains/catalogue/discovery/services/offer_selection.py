"""
One product, several suppliers: which offer does THIS shop see?

THE FILE THAT CANNOT BE COPIED QUICKLY, and the reason the catalogue is
worth maintaining. Without a resolved catalogue the question is not
hard, it is UNASKABLE -- "WHT SUGR 2.5KG" and "White Sugar 2.5kg" are
unrelated strings, and there is no group to choose within. With it,
every group is a real decision about whose sugar a particular shop is
shown.

IT IS ALSO THE MOST PRODUCT-SENSITIVE FUNCTION IN THE SYSTEM. Lead with
price and TruConnect becomes a price comparison site that happens to
have suppliers on it; lead with relationship and it is loyal but
possibly expensive. That choice decides how the platform FEELS, and it
is one line below.

THE CURRENT RULE, and it is a recommendation awaiting Mandla's decision
(docs/v2/V2_15 Book Two, Part 15 q3):

    1  BUYABLE AT ALL        out of stock, or a rail this shop cannot
                             pay on, is not an option. An unbuyable
                             card is worse than no card.
    2  THEIR OWN SUPPLIER    if this shop already buys from one of
                             them, that one. Switching suppliers is a
                             RELATIONSHIP decision and the feed should
                             not make it quietly on somebody's behalf.
    3  CHEAPEST              otherwise, the best price wins.
    4  STABLE TIE-BREAK      by offer id, so the same group resolves
                             the same way on every refresh. A card that
                             changes supplier under a thumb is one
                             nobody can trust.

WHAT IT DELIBERATELY DOES NOT KNOW: who the supplier is, how big their
catalogue is, how long they have been here, or whether they pay us.
Sponsorship is a LABELLED slot the engine injects (V2_15 Book Two Part
8), never a thumb on this scale.
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Set
from uuid import UUID


def select(
    offers: List,
    *,
    in_stock_ids: Optional[Set] = None,
    incumbent_supplier_ids: Optional[Set[str]] = None,
    payable_supplier_ids: Optional[Set[str]] = None,
):
    """The one offer to show, or None when none is worth showing.

    EVERY INPUT IS A PRE-BUILT SET, never something to look up here.
    Eleven needs each asking "is this in stock, can I pay them, do I
    buy from them" is the N+1 this codebase has written and removed
    twice in one week. The caller batches once; this decides.

    in_stock_ids is None means UNKNOWN, not "nothing is in stock" --
    a caller that has not checked must not have its cards silently
    emptied.
    """
    if not offers:
        return None

    candidates = list(offers)

    if in_stock_ids is not None:
        buyable = [o for o in candidates if o.id in in_stock_ids]
        # If NOTHING is in stock, fall back to showing the group anyway
        # rather than hiding the product entirely. "Out of stock" is
        # information a shop can act on -- ask, wait, look elsewhere --
        # and silence is not.
        candidates = buyable or candidates

    if payable_supplier_ids is not None:
        payable = [o for o in candidates if str(o.supplier_profile_id) in payable_supplier_ids]
        # No fallback here, unlike stock: an offer from a supplier this
        # shop has no way to pay is not a weaker option, it is a dead
        # end at the last step of checkout.
        candidates = payable
        if not candidates:
            return None

    if incumbent_supplier_ids:
        mine = [o for o in candidates if str(o.supplier_profile_id) in incumbent_supplier_ids]
        if mine:
            candidates = mine

    return sorted(candidates, key=lambda o: (o.price_cents, str(o.id)))[0]


def select_all(
    groups: Iterable[List],
    *,
    in_stock_ids: Optional[Set] = None,
    incumbent_supplier_ids: Optional[Set[str]] = None,
    payable_supplier_ids: Optional[Set[str]] = None,
) -> List:
    """select() across many groups, dropping the ones with no viable
    offer. The plural is the signature callers should reach for -- a
    single-group version WILL be used in a loop."""
    chosen = []
    for group in groups:
        offer = select(
            group,
            in_stock_ids=in_stock_ids,
            incumbent_supplier_ids=incumbent_supplier_ids,
            payable_supplier_ids=payable_supplier_ids,
        )
        if offer is not None:
            chosen.append(offer)
    return chosen


def alternatives_count(group: List, chosen) -> int:
    """How many OTHER suppliers carry this same product.

    ONLY MEANINGFUL WHEN MATCHING HAS DONE ITS WORK, and that is the
    point: "also from 3 suppliers" on a card is the resolved catalogue
    made visible, and it is the one thing on the screen a competitor
    without one cannot draw.

    A COUNT, NEVER A LEAGUE TABLE. V2_04 2.4 is explicit -- comparison
    is framed as a saving for the buyer, never as suppliers ranked
    against each other.
    """
    if chosen is None:
        return 0
    return max(0, len(group) - 1)
