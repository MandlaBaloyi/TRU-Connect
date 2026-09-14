"""
How often does this business usually order from this supplier, and are
they overdue?

THE ROW THIS MAKES POSSIBLE (V2_04 §3.3, section 2):

    "Thabo's Corner Shop -- usually orders weekly, nothing for 3 weeks"

V2_04 calls that "a phone call worth making", and it is the section
that turns the supplier's Community tab from an inbox into a sales
tool. No privacy question at all: it is the supplier's own customers
and their own trading history with them.

MEAN INTERVAL, NOT MEDIAN OR A MODEL. With three or four orders to
work from -- which is what a real early-stage supplier has -- a median
is the same number as a mean and a fitted model is a fiction. The
honest computation for this data volume is the simple one, and
replacing it later is a change to one function.

  ─────────────────────────────────────────────────────────────────────
  TWO ORDERS IS THE MINIMUM, because one order has no interval. A
  business that has ordered once is not "overdue" -- they are new, and
  calling them overdue would be the platform inventing a pattern from
  a single point.
  ─────────────────────────────────────────────────────────────────────

SUBMITTED ORDERS ONLY. A cart is not an order, and a cancelled or
declined one says nothing about a buying rhythm -- counting either
would make a supplier who declines a lot look like they have loyal
customers.

OVERDUE IS A RATIO, NOT A FIXED NUMBER OF DAYS. A shop that orders
every week is overdue at ten days; one that orders monthly is not
overdue until well past forty. A single day-count threshold would spam
the first supplier and never fire for the second.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

#: How far past the usual gap before a customer counts as quiet.
#: 1.5x -- a week's shopper is flagged at ten days, a monthly one at
#: about six weeks. Chosen to be late enough that normal variation does
#: not trigger it, and early enough that the call is still worth making.
OVERDUE_MULTIPLIER = 1.5

#: Fewer than this many orders and there is no rhythm to be late
#: against. Two gives exactly one interval, which is thin but real.
MIN_ORDERS_FOR_A_PATTERN = 2


@dataclass(frozen=True)
class ReorderPattern:
    """What we can say about one business's buying rhythm."""

    order_count: int
    last_order_at: Optional[datetime]
    #: None when there is no pattern yet -- see MIN_ORDERS_FOR_A_PATTERN.
    typical_gap_days: Optional[float]
    days_since_last: Optional[float]

    @property
    def is_overdue(self) -> bool:
        if self.typical_gap_days is None or self.days_since_last is None:
            return False
        return self.days_since_last > self.typical_gap_days * OVERDUE_MULTIPLIER

    @property
    def days_overdue(self) -> Optional[float]:
        if not self.is_overdue or self.typical_gap_days is None:
            return None
        return round(self.days_since_last - self.typical_gap_days, 1)


def pattern_from(order_dates: List[datetime], now: datetime) -> ReorderPattern:
    """Build a pattern from this business's order timestamps.

    Takes DATES rather than orders, and `now` rather than reading the
    clock, so the whole computation is a pure function -- which is what
    makes the overdue arithmetic testable without seeding a database
    three weeks in the past.
    """
    dates = sorted(d for d in order_dates if d is not None)
    if not dates:
        return ReorderPattern(0, None, None, None)

    last = dates[-1]
    days_since = round((now - last).total_seconds() / 86400, 1)

    if len(dates) < MIN_ORDERS_FOR_A_PATTERN:
        # A real customer, with no rhythm to be late against yet.
        return ReorderPattern(len(dates), last, None, days_since)

    gaps = [
        (dates[i] - dates[i - 1]).total_seconds() / 86400 for i in range(1, len(dates))
    ]
    typical = round(sum(gaps) / len(gaps), 1)
    return ReorderPattern(len(dates), last, typical, days_since)
