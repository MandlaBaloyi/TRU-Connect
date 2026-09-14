"""
OBSERVED signals: what the shop actually did.

THE EVIDENCE HALF. Declared signals are what somebody said about their
own shop while filling in a form -- useful, immediate, and a hypothesis.
This is what they paid for.

IT READS ORDERS, NOT SUPPLIERS, and the difference is the whole reason
this module is allowed to exist inside demand/. The orders domain
answers with categories, dates and amounts; the join to supplier_offers
happens there, where it is permitted. Nothing here can name a supplier
even if it wanted to -- see the repository's own comment, and
tests/architecture/test_demand_independence.py.

WHY THAT IS NOT A LOOPHOLE. The invariant is that the model describes
the SHOP. A shop's own purchase history IS the shop -- it is the most
direct evidence of what they need that exists. What the model must never
contain is who sold it to them, and it does not.

SLOW TO ARRIVE, WHICH IS THE POINT OF DECLARED SIGNALS EXISTING. A shop
has nothing here on day one, something after a week, and a rhythm after
a month or two.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.core.base_model import utcnow
from src.shared.algorithms import reorder_gap


@dataclass(frozen=True)
class ObservedSignals:
    """What the order history says, with nothing inferred yet."""

    #: {category: how many order lines}. The raw count, not a weight --
    #: turning counts into weights is reconciliation's job, and a signal
    #: that pre-scores itself scatters the weighting across six files.
    category_counts: Dict[str, int] = field(default_factory=dict)

    order_count: int = 0
    #: Measured days between orders. None until there are two, because
    #: one order is not a pattern -- the same rule the supplier feed and
    #: the relationship ledger already follow.
    measured_gap_days: Optional[float] = None
    days_since_last_order: Optional[float] = None
    #: Median rather than mean: one bulk order at month-end should not
    #: drag the typical basket up for the eleven ordinary ones.
    typical_order_cents: Optional[int] = None

    @property
    def is_empty(self) -> bool:
        return self.order_count == 0

    @property
    def total_lines(self) -> int:
        return sum(self.category_counts.values())


def read(business_id) -> ObservedSignals:
    """Everything the order history says about this shop.

    TWO QUERIES, NOT ONE PER CATEGORY. The whole picture arrives in a
    fixed number of reads however long the shop has been trading.
    """
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    counts = StockOrderRepository.category_purchase_counts(business_id)
    rows = StockOrderRepository.purchase_dates_and_totals(business_id)

    if not rows:
        return ObservedSignals(category_counts=counts)

    dates = [row[0] for row in rows if row[0] is not None]
    totals = sorted(row[1] for row in rows if row[1] is not None)

    # REUSES THE SUPPLIER FEED'S OWN RHYTHM MATHS. reorder_gap moved to
    # shared/algorithms precisely so a second caller could have it
    # without importing the composer -- this is that second caller.
    pattern = reorder_gap.pattern_from(dates, utcnow())

    return ObservedSignals(
        category_counts=counts,
        order_count=pattern.order_count,
        measured_gap_days=pattern.typical_gap_days,
        days_since_last_order=pattern.days_since_last,
        typical_order_cents=_median(totals),
    )


def _median(values: List[int]) -> Optional[int]:
    """Median, not mean.

    A shop that buys R600 weekly and once bought a R9,000 pallet has a
    typical basket of R600. The mean would say R1,300 and the feed would
    start hiding the things they actually buy.
    """
    if not values:
        return None
    middle = len(values) // 2
    if len(values) % 2:
        return int(values[middle])
    return int((values[middle - 1] + values[middle]) / 2)
