"""
When what a shop SAID and what a shop DID disagree.

THE CASE THIS WHOLE FILE EXISTS FOR:

    A shop declares bread. Six months of orders contain no bread.

    THE WRONG READING: they lied, drop the signal.
    THE RIGHT READING: THEY BUY BREAD SOMEWHERE ELSE.

Getting that backwards would delete the most commercially valuable
thing the engine can notice -- a need the shop has already CONFIRMED it
has, that TruConnect is losing to somebody else. Aggregated, that is a
supplier acquisition target with a number attached.

The rules are tested on plain values rather than through the database:
the judgement is the valuable part, it is a pure function, and pinning
it as one keeps these tests fast enough to run on every change.
"""
from __future__ import annotations

from src.domains.business.demand.services import reconciliation


class TestTheCaseThatMatters:
    def test_a_declared_category_never_bought_here_survives_as_unserved(self):
        """NOT DELETED, NOT DOWNGRADED TO NOISE. It is a confirmed need
        we are failing to meet."""
        needs = reconciliation.merge(["BAKERY"], {"BEVERAGES": 10})

        bakery = next(n for n in needs if n["category"] == "BAKERY")
        assert bakery["unserved"] is True
        assert bakery["weight"] == 1.0, "a contradicted declaration keeps its weight"
        assert bakery["source"] == "declared"
        assert reconciliation.unserved_categories(needs) == ["BAKERY"]

    def test_declaring_and_buying_is_the_strongest_signal(self):
        """Said it, then proved it."""
        needs = reconciliation.merge(["BAKERY"], {"BAKERY": 12})

        bakery = next(n for n in needs if n["category"] == "BAKERY")
        assert bakery["source"] == "both"
        assert bakery["unserved"] is False
        assert bakery["confidence"] > 0.9

    def test_buying_something_never_declared_is_added_not_ignored(self):
        """A FORM IS NOT AN INVENTORY. Shops buy things they did not
        think to mention, and behaviour outranks a memory of the shop."""
        needs = reconciliation.merge(["BAKERY"], {"BAKERY": 5, "HOUSEHOLD_CLEANING": 4})

        cleaning = next(n for n in needs if n["category"] == "HOUSEHOLD_CLEANING")
        assert cleaning["source"] == "observed"
        assert cleaning["weight"] > 0


class TestHowMuchEvidenceIsEnough:
    def test_one_purchase_is_an_experiment_not_a_habit(self):
        once = reconciliation.merge([], {"BAKERY": 1})[0]
        often = reconciliation.merge([], {"BAKERY": 20})[0]

        assert once["confidence"] < often["confidence"]

    def test_confidence_never_reaches_certainty(self):
        """Forty purchases is strong evidence of a habit and still not
        proof of next month. A model that reaches 1.0 has stopped being
        able to learn that shops change."""
        needs = reconciliation.merge([], {"BAKERY": 500})

        assert needs[0]["confidence"] <= 0.95

    def test_a_category_they_buy_constantly_outranks_one_they_tried(self):
        needs = reconciliation.merge([], {"BAKERY": 40, "ELECTRONICS_ACCESSORIES": 1})

        assert needs[0]["category"] == "BAKERY"


class TestItIsDeterministic:
    def test_the_same_inputs_give_the_same_order(self):
        """A feed whose order changes between identical requests is one
        nobody can debug."""
        first = reconciliation.merge(["BAKERY", "BEVERAGES"], {"MEAT_FROZEN": 3})
        second = reconciliation.merge(["BEVERAGES", "BAKERY"], {"MEAT_FROZEN": 3})

        assert [n["category"] for n in first] == [n["category"] for n in second]

    def test_nothing_declared_and_nothing_bought_is_nothing(self):
        assert reconciliation.merge([], {}) == []
        assert reconciliation.unserved_categories([]) == []
