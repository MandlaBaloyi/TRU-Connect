"""
What a shop can plausibly spend on ONE product.

THE FAILURE THIS PREVENTS: a spaza whose median order is R600 opening
the app to a R9,000 pallet at the front of "Stock for your shop". The
card is not wrong about the category -- it is wrong about the shop, and
it teaches the owner that the rail is not really about them.

Tested as plain values because that is what it is: no fixture, no
database, and the reasoning readable in one screen.
"""
from __future__ import annotations

from src.domains.business.demand.algorithms import weighting


class TestMeasuredBeatsDeclared:
    def test_a_measured_basket_sets_the_ceiling(self):
        """Real baskets say more than a band picked off a form once --
        the same rule cadence already follows."""
        ceiling = weighting.max_line_cents(
            typical_order_cents=60_000, declared_ceiling_cents=50_000
        )

        assert ceiling == 90_000  # R600 median -> R900 a line

    def test_the_declared_band_is_used_until_they_have_ordered(self):
        assert (
            weighting.max_line_cents(
                typical_order_cents=None, declared_ceiling_cents=50_000
            )
            == 50_000
        )


class TestUnknownStaysUnknown:
    def test_a_shop_we_know_nothing_about_gets_no_ceiling(self):
        """None means DO NOT FILTER. Inventing a number here would hide
        stock from the shops we know least about -- exactly the ones who
        can least afford a feed that quietly omits things (flaw B.5)."""
        assert weighting.max_line_cents(None, None) is None

    def test_a_shop_over_ten_thousand_a_week_gets_no_ceiling(self):
        """OVER_10000 maps to None on purpose: there is no sensible top
        for a buyer whose band has no upper bound."""
        assert weighting.max_line_cents(None, weighting.SPEND_BAND_ORDER_CEILING_CENTS["OVER_10000"]) is None

    def test_a_zero_basket_is_not_a_zero_ceiling(self):
        """A shop with orders totalling nothing is a data artefact, not
        a shop that can spend nothing. Falling through to declared beats
        computing a ceiling of 0, which would empty their feed."""
        assert weighting.max_line_cents(0, 50_000) == 50_000
