"""
Ordering a page by what this shop can plausibly spend.

THE RULE, AND IT IS THE INTERESTING PART: this ORDERS and never
REMOVES. Filtering by price would hide the R9,000 pallet from a spaza,
which is usually right and catastrophic when it is wrong -- the shop is
never told anything is missing. Flaw B.2 calls silence the one
unacceptable outcome.

Ordering gets the same result where it matters. The feed takes the
first N, so the pallet falls off the end of a personalised rail on its
own, while a shop that deliberately taps "Grains" and scrolls still
finds it -- because there it is the catalogue, not a recommendation.
"""
from __future__ import annotations

from src.domains.catalogue.discovery.services.browse_service import _affordable_first


def _card(id_, price):
    return {"id": id_, "priceCents": price}


class TestAffordableThingsComeFirst:
    def test_the_pallet_moves_behind_the_bag(self):
        cards = [_card("pallet", 900_000), _card("bag", 12_000)]

        assert [c["id"] for c in _affordable_first(cards, 90_000)] == ["bag", "pallet"]

    def test_nothing_is_ever_dropped(self):
        """The whole argument for ordering instead of filtering."""
        cards = [_card("pallet", 900_000), _card("crate", 500_000)]

        ordered = _affordable_first(cards, 90_000)

        assert len(ordered) == 2, "a shop that can afford none of it still sees it"

    def test_order_among_affordable_cards_is_untouched(self):
        """STABLE: whatever ranking produced the page survives inside
        each half -- offer_selection already made a real decision here."""
        cards = [_card("b", 10_000), _card("a", 5_000), _card("c", 20_000)]

        assert [c["id"] for c in _affordable_first(cards, 90_000)] == ["b", "a", "c"]

    def test_a_card_exactly_at_the_ceiling_is_affordable(self):
        cards = [_card("over", 90_001), _card("exact", 90_000)]

        assert [c["id"] for c in _affordable_first(cards, 90_000)] == ["exact", "over"]


class TestUnknownIsANoOp:
    def test_no_ceiling_leaves_the_page_alone(self):
        """Most shops have neither a basket nor a declared band, and
        their page must come back exactly as the catalogue ranked it."""
        cards = [_card("pallet", 900_000), _card("bag", 12_000)]

        assert _affordable_first(cards, None) == cards

    def test_a_card_with_no_price_is_treated_as_affordable(self):
        """Missing price is unknown, not expensive -- sinking it would
        punish an offer for a gap in its own data."""
        cards = [_card("priced", 900_000), _card("unpriced", None)]

        assert [c["id"] for c in _affordable_first(cards, 90_000)] == ["unpriced", "priced"]
