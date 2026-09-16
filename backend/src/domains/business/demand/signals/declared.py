"""
DECLARED signals: what the shop told us.

WHAT MAKES THIS WORTH READING AT ALL. Before the C.1 reshape the form
asked what a shop SELLS from a per-category list of adjectives, and for
five of the eight business categories -- including RETAIL, which is what
a spaza would pick -- the available answer was the word "Products".
There was nothing here to read.

It now asks what they BUY, against the seventeen real ProductCategory
values, so a declaration lands directly on the vocabulary the catalogue
and the feed already speak. No mapping table, and nothing to drift.

IT IS A HYPOTHESIS, NOT EVIDENCE. Everything here is what somebody said
about their own shop at a moment they were filling in a form. That is
genuinely useful -- it is the only thing available on day one, and it is
what turns a cold start into a warm one -- but observation outranks it
the moment observation exists (Book Three Part 6).

NO SUPPLIER ANYTHING. Enforced by
tests/architecture/test_demand_independence.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class DeclaredSignals:
    """Everything the profile form contributes to the model.

    ALL OPTIONAL, AND ABSENCE IS NOT ZERO. A shop that answered nothing
    is unknown, not empty-handed -- the difference decides whether the
    feed leans on this model or falls back to platform-wide defaults.
    """

    categories: List[str] = field(default_factory=list)
    customer_types: List[str] = field(default_factory=list)
    restock_rhythm: Optional[str] = None
    weekly_spend_band: Optional[str] = None
    employee_range: Optional[str] = None
    city_or_town: Optional[str] = None
    has_location: bool = False
    #: "COLLECT", "DELIVERY", "BOTH", or None for "not asked". FOUR
    #: states, and the last is load-bearing -- see the column's own
    #: comment. Nothing downstream may collapse None into an answer.
    stock_collection: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        return not self.categories and not self.restock_rhythm and not self.weekly_spend_band


def read(business_id) -> DeclaredSignals:
    """Read the profile, or return empty signals if there is none.

    A MISSING PROFILE IS NOT AN ERROR. The row is created lazily on
    first access, so a business that has never opened the screen simply
    has nothing to declare -- and the feed must work for them.
    """
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    profile = BusinessProfileRepository.get_for_business(business_id)
    if profile is None:
        return DeclaredSignals()

    return DeclaredSignals(
        categories=list(profile.buys_categories or []),
        customer_types=list(profile.customer_types or []),
        restock_rhythm=profile.restock_rhythm.value if profile.restock_rhythm else None,
        weekly_spend_band=(
            profile.weekly_spend_band.value if profile.weekly_spend_band else None
        ),
        employee_range=profile.employee_range.value if profile.employee_range else None,
        city_or_town=profile.city_or_town,
        has_location=profile.latitude is not None and profile.longitude is not None,
        stock_collection=(
            profile.stock_collection.value if profile.stock_collection else None
        ),
    )
