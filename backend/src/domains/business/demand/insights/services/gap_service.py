"""
Demand we are failing to meet.

THE MOST PERSUASIVE NUMBER THE PLATFORM CAN PRODUCE (V2_15 Book Three
Part 10): "412 shops tell us they sell airtime, and not one of them has
ever bought airtime here." That is a product gap, a supplier
acquisition target and a slide, and none of it required asking anybody
a new question -- it falls out of the reconciliation rule the feed
already runs.

IT REUSES reconciliation.merge RATHER THAN RE-ASKING IN SQL. The rule
for what counts as unserved is a product decision with a paragraph of
reasoning behind it (declared, never bought HERE, never silently
dropped). Re-expressing that as a LEFT JOIN would put the rule in two
places, and the SQL copy would be the one nobody updates. Two queries
feed the same Python rule the feed uses, per shop, in memory.

TWO QUERIES FOR THE WHOLE PLATFORM, not two per shop. The declared
side is one column scan; the observed side is one GROUP BY. Everything
after that is arithmetic.

WHAT IT DELIBERATELY CANNOT SAY, and each omission is a decision:

  WHO. No shop is ever named or returned. The output is counts per
  category and nothing else -- see MIN_SHOPS_TO_REPORT.

  WHETHER WE STOCK IT. "Nobody buys airtime here" and "nobody SELLS
  airtime here" are different facts, and the second one lives in
  supplier offers, which this package may never read
  (tests/architecture/test_demand_independence.py). Cross-referencing
  the two is a job for something allowed to import both -- and it is a
  composition, not a reason to weaken the boundary.

  WHERE. Geographic gaps are named in Part 10 and are not buildable:
  flaw B.5, most shops have no coordinates. A map drawn from two
  located shops would be a confident lie.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from src.domains.business.demand.services import reconciliation

#: Fewest shops a category may represent and still be reported.
#:
#: AN AGGREGATE OF ONE IS NOT AN AGGREGATE. "1 shop in Diepsloot needs
#: airtime" is a sentence about a person, and the moment a number like
#: that reaches a supplier it stops being a market fact and becomes
#: surveillance (Part 12). Three is the smallest group that does not
#: identify its members by arithmetic.
#:
#: FALSIFIED BY: nothing about the data -- this is a privacy floor, not
#: a guess. It moves only if the rule about what suppliers may see
#: moves.
MIN_SHOPS_TO_REPORT = 3


def unserved_by_category(min_shops: Optional[int] = None) -> dict:
    """Categories shops say they need and do not buy here.

    min_shops LOWER THAN THE DEFAULT IS FOR INTERNAL INSPECTION ONLY --
    a founder counting a pilot of four shops, or a test. Nothing
    produced with a lowered threshold may be shown to a supplier, which
    is why the default is the safe one and the caller has to say
    otherwise in writing.
    """
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    threshold = MIN_SHOPS_TO_REPORT if min_shops is None else min_shops

    declared = BusinessProfileRepository.declared_categories_by_business()
    bought = StockOrderRepository.category_purchase_counts_by_business()

    declaring: Dict[str, int] = {}
    unserved: Dict[str, int] = {}

    for business_id, categories in declared.items():
        # THE SAME RULE THE FEED RUNS, per shop. A category they
        # declared and have bought is served; one they declared and
        # have never bought here is the gap, whether they buy it
        # elsewhere or nobody sells it -- and from this side those two
        # look identical, which is honest.
        needs = reconciliation.merge(categories, bought.get(business_id, {}))

        for category in categories:
            declaring[category] = declaring.get(category, 0) + 1
        for category in reconciliation.unserved_categories(needs):
            unserved[category] = unserved.get(category, 0) + 1

    rows = [
        {
            "category": category,
            "shopsDeclaring": declaring.get(category, 0),
            "shopsUnserved": count,
            # What share of the shops that want this are not getting it
            # here. A category 100% unserved is a hole; one at 20% is a
            # supplier who cannot keep up.
            "shareUnserved": round(count / declaring[category], 3)
            if declaring.get(category)
            else 0.0,
        }
        for category, count in unserved.items()
    ]

    reportable = [r for r in rows if r["shopsUnserved"] >= threshold]

    # BIGGEST GAP FIRST, and deterministic on ties so two runs of the
    # same report do not disagree about the order.
    reportable.sort(key=lambda r: (-r["shopsUnserved"], r["category"]))

    return {
        "categories": reportable,
        # NEVER SILENTLY WITHHELD. A report that quietly drops the
        # categories below the threshold reads as "no gaps there",
        # which is the opposite of what it means (flaw B.2: silence is
        # the one unacceptable outcome). Saying how many were held back
        # costs one integer.
        "suppressed": len(rows) - len(reportable),
        "shopsConsidered": len(declared),
        "minShops": threshold,
    }


def unserved_for_shops(business_ids: List[str]) -> dict:
    """The same question for a named subset -- a pilot, a township, a
    supplier's own delivery area once radius exists.

    IT TAKES IDS AND RETURNS NONE, which is the only shape that stays
    safe: the caller already knows which shops it asked about, so
    returning them tells nobody anything new, while the result remains
    counts per category.
    """
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    wanted = {str(b) for b in business_ids}
    declared = {
        business_id: categories
        for business_id, categories in BusinessProfileRepository.declared_categories_by_business().items()
        if business_id in wanted
    }
    bought = StockOrderRepository.category_purchase_counts_by_business()

    unserved: Dict[str, int] = {}
    for business_id, categories in declared.items():
        needs = reconciliation.merge(categories, bought.get(business_id, {}))
        for category in reconciliation.unserved_categories(needs):
            unserved[category] = unserved.get(category, 0) + 1

    return {
        "categories": sorted(
            ({"category": c, "shopsUnserved": n} for c, n in unserved.items()),
            key=lambda r: (-r["shopsUnserved"], r["category"]),
        ),
        "shopsConsidered": len(declared),
    }
