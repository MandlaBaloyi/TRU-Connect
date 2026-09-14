"""
What is moving fast right now.

THE DISTINCTION THIS RAIL LIVES OR DIES ON: a bestseller is a product
that has always sold well, and a shopkeeper already knows about it. This
is a product selling faster THAN ITSELF -- a change, not a level. If
these tests ever pass while the rail fills with the same big sellers
every week, the rail has quietly become a leaderboard and is worth less
than the space it occupies.

Tested as plain maps because that is what the algorithm takes: the
repository fetches two windows, and the judgement here is a pure
function that can be read in one screen.
"""
from __future__ import annotations

from src.domains.network.community.algorithms import velocity


def _steady(units_per_day: float) -> dict:
    """A product selling at the same rate in both windows."""
    return {
        "recent": {"p": round(units_per_day * velocity.RECENT_DAYS)},
        "baseline": {"p": round(units_per_day * velocity.BASELINE_DAYS)},
    }


class TestItFindsChangeNotVolume:
    def test_a_steady_seller_never_qualifies(self):
        """THE WHOLE POINT. A product selling forty a week, every week,
        is a bestseller and is not news."""
        window = _steady(40)

        assert velocity.rising_products(window["recent"], window["baseline"]) == []

    def test_a_product_selling_faster_than_itself_qualifies(self):
        recent = {"p": 40}       # ~5.7/day over 7 days
        baseline = {"p": 56}     # 2.0/day over 28 days

        assert velocity.rising_products(recent, baseline) == ["p"]

    def test_a_small_product_can_outrank_a_big_one(self):
        """Comparing across products would rank a case of 24 above a
        loaf forever, and the rail would become a list of things that
        come in big boxes."""
        recent = {"small": 10, "big": 100}
        baseline = {"small": 8, "big": 360}  # small tripled its rate; big flat

        assert velocity.rising_products(recent, baseline)[0] == "small"

    def test_the_rates_are_per_day_not_per_window(self):
        """7 days of units against 28 days of units compared directly
        would make almost nothing look like it was rising."""
        # Exactly the same daily rate in both windows.
        recent = {"p": 7}
        baseline = {"p": 28}

        assert velocity.rising_products(recent, baseline) == []


class TestItResistsTinyNumbers:
    def test_one_sale_against_nothing_is_not_a_spike(self):
        """Without a floor, one unit last week against zero the month
        before is an infinite increase, and the rail fills with things
        exactly one person bought once."""
        assert velocity.rising_products({"p": 1}, {}) == []

    def test_a_genuinely_busy_new_product_still_qualifies(self):
        """A product with no baseline is NEW, not infinite. It has to
        clear the units floor on its own merit."""
        assert velocity.rising_products({"p": velocity.MIN_RECENT_UNITS + 5}, {}) == ["p"]

    def test_a_product_that_slowed_down_is_excluded(self):
        recent = {"p": 5}
        baseline = {"p": 200}

        assert velocity.rising_products(recent, baseline) == []


class TestItIsDeterministic:
    def test_the_same_inputs_give_the_same_order(self):
        """A rail that reorders between identical requests is one nobody
        can debug."""
        recent = {"a": 20, "b": 20, "c": 20}
        baseline = {"a": 20, "b": 20, "c": 20}

        first = velocity.rising_products(recent, baseline)
        second = velocity.rising_products(dict(reversed(list(recent.items()))), baseline)

        assert first == second

    def test_limit_takes_the_strongest_risers(self):
        recent = {"weak": 10, "strong": 60}
        baseline = {"weak": 24, "strong": 28}

        assert velocity.rising_products(recent, baseline, limit=1) == ["strong"]

    def test_nothing_sold_is_nothing_rising(self):
        assert velocity.rising_products({}, {}) == []
