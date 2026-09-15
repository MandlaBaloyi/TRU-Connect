"""
The feed leaning on the demand engine (V2_15 Part 14, Phase 2).

TWO THINGS THE RAIL OWES A SHOP, and both are tested on real
ShopNeeds objects rather than fakes, because the point is that the
feed reads the engine's OUTPUT -- a stub would let the two drift.

  1  OPEN WITH WHAT THEY NEED MOST. The catalogue has no opinion about
     this shop; the engine does, so the ordering happens on this side.
  2  SAY SOMETHING TRUE ABOUT WHY. "Based on what you told us you buy"
     is a lie to a shop that never filled the form.
"""
from __future__ import annotations

from src.domains.business.demand.services.needs_service import CategoryNeed, ShopNeeds
from src.domains.network.community.business import sections
from src.domains.network.community.services import feed_detail_service


def _needs(*pairs) -> ShopNeeds:
    """ShopNeeds from (category, weight, source) triples."""
    return ShopNeeds(
        categories=[
            CategoryNeed(category=c, weight=w, confidence=0.8, source=s)
            for c, w, s in pairs
        ]
    )


class TestTheRailOpensWithTheStrongestNeed:
    def test_the_heaviest_category_leads(self):
        products = [
            {"id": "1", "category": "ELECTRONICS_ACCESSORIES"},
            {"id": "2", "category": "BAKERY"},
        ]
        needs = _needs(("BAKERY", 1.0, "both"), ("ELECTRONICS_ACCESSORIES", 0.4, "observed"))

        ordered = feed_detail_service.strongest_needs_first(products, needs)

        assert [p["id"] for p in ordered] == ["2", "1"]

    def test_order_inside_a_category_is_preserved(self):
        """STABILITY IS LOAD-BEARING: browse_service has already put the
        affordable cards first, and a sort that reshuffled within a
        category would throw that away."""
        products = [
            {"id": "cheap", "category": "BAKERY"},
            {"id": "pallet", "category": "BAKERY"},
        ]

        ordered = feed_detail_service.strongest_needs_first(products, _needs(("BAKERY", 1.0, "both")))

        assert [p["id"] for p in ordered] == ["cheap", "pallet"]

    def test_a_category_the_shop_does_not_need_sinks_rather_than_vanishing(self):
        """It came back from the catalogue, so it stays -- last."""
        products = [
            {"id": "stray", "category": "TOOLS_HARDWARE"},
            {"id": "bread", "category": "BAKERY"},
        ]

        ordered = feed_detail_service.strongest_needs_first(products, _needs(("BAKERY", 1.0, "both")))

        assert [p["id"] for p in ordered] == ["bread", "stray"]
        assert len(ordered) == 2

    def test_a_card_with_no_category_does_not_crash_the_rail(self):
        """Unmatched offers become their own group in the browse
        repository and can arrive without one."""
        products = [{"id": "x", "category": None}, {"id": "bread", "category": "BAKERY"}]

        ordered = feed_detail_service.strongest_needs_first(products, _needs(("BAKERY", 1.0, "both")))

        assert [p["id"] for p in ordered] == ["bread", "x"]


class TestTheRailExplainsItselfTruthfully:
    def test_a_shop_that_only_declared_is_told_so(self):
        assert (
            sections._why_this_rail(_needs(("BAKERY", 1.0, "declared")))
            == "Based on what you told us you buy"
        )

    def test_a_shop_that_never_filled_the_form_is_not_told_it_did(self):
        """THE LIE PHASE 1 INTRODUCED. This shop's needs came entirely
        from its own orders; "what you told us" would read as a guess."""
        assert (
            sections._why_this_rail(_needs(("BAKERY", 1.0, "observed")))
            == "Based on what you buy"
        )

    def test_a_shop_with_both_is_told_both(self):
        needs = _needs(("BAKERY", 1.0, "both"), ("BEVERAGES", 0.6, "observed"))

        assert sections._why_this_rail(needs) == "Based on what you buy and what you told us"
