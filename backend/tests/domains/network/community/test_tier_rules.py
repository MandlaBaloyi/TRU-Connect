"""
What a supplier's plan actually moves.

    TIER MAY BREAK A TIE. IT MAY NEVER BEAT A FACT.

WHAT THESE DEFEND, worst consequence first:

  AN EXPIRED PLAN IS FREE, IMMEDIATELY. A lapsed plan that keeps its
  reach until a nightly job notices is reach nobody paid for -- taken
  from the supplier who did pay. This is the one that costs real money
  if it is wrong, in both directions.

  A BUG COSTS REACH, IT NEVER GRANTS IT. Every unreadable state --
  missing profile, unknown tier, absent column -- resolves to FREE.

  THE FACT RANKS FIRST. Whether a shop already knows a supplier
  separates the list before any plan is consulted, at every tier.

  THE ORDER IS DETERMINISTIC. A rail that reshuffles between identical
  requests is one nobody can debug, and one nobody can be shown to have
  been treated fairly by.
"""
from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from src.core.base_model import utcnow
from src.domains.network.community.placement import tie_break, tier_rules


def _profile(tier=None, expires=None, name="A", ident="1"):
    """A stand-in, because none of these rules touch the database."""
    return SimpleNamespace(
        id=ident, business_name=name, plan_tier=tier, plan_expires_at=expires
    )


class TestAnExpiredPlanIsFree:
    def test_a_lapsed_plan_loses_its_reach_immediately(self):
        """THE ONE THAT COSTS REAL MONEY IF IT IS WRONG. Reach that
        outlives the payment is taken from a supplier who is paying."""
        lapsed = _profile(tier="MAX", expires=utcnow() - timedelta(days=1))

        assert tier_rules.effective_tier(lapsed) == "FREE"

    def test_a_current_plan_keeps_its_reach(self):
        live = _profile(tier="MAX", expires=utcnow() + timedelta(days=30))

        assert tier_rules.effective_tier(live) == "MAX"

    def test_no_expiry_means_it_does_not_expire(self):
        """Right for FREE and for an open-ended subscription. Only a
        trial or a PARTNER agreement sets a date."""
        assert tier_rules.effective_tier(_profile(tier="PRO", expires=None)) == "PRO"


class TestABugCostsReachRatherThanGrantingIt:
    def test_a_missing_profile_is_free(self):
        assert tier_rules.effective_tier(None) == "FREE"

    def test_an_unknown_tier_is_free(self):
        """A value this module has never heard of -- a new enum member,
        a bad migration -- must not be treated as the top plan."""
        assert tier_rules.effective_tier(_profile(tier="PLATINUM")) == "FREE"

    def test_a_profile_without_the_column_is_free(self):
        assert tier_rules.effective_tier(SimpleNamespace(id="1")) == "FREE"

    def test_an_unknown_tier_gets_the_free_cap(self):
        assert tier_rules.absolute_cap("PLATINUM") == tier_rules.DEFAULT_CAP
        assert tier_rules.absolute_cap(None) == tier_rules.DEFAULT_CAP


class TestTheCeilingIsAPricingLeverNotADoor:
    def test_the_steps_are_small(self):
        """A plan that DOUBLED a supplier's presence would be selling
        domination by instalments."""
        caps = [tier_rules.absolute_cap(t) for t in ("FREE", "PRO", "MAX")]

        assert caps == sorted(caps), "a higher plan must never hold fewer cards"
        assert caps[-1] <= caps[0] * 2, "no plan may double a supplier's presence"

    def test_even_the_top_plan_leaves_a_rail_a_market(self):
        """Against interleave's 40% proportional ceiling, a MAX
        supplier's cap binds down on a normal rail -- so a rail is never
        fewer than three distinct suppliers."""
        from src.domains.network.community.algorithms import interleave

        effective = interleave.effective_cap(tier_rules.absolute_cap("MAX"), rail_size=12)

        assert effective <= 4


class TestTheToleranceBand:
    def test_two_kilometres_apart_is_the_same_trip(self):
        assert tier_rules.within_band(1.0, 2.5) is True

    def test_five_kilometres_apart_is_not(self):
        assert tier_rules.within_band(1.0, 6.0) is False

    def test_unknown_is_never_tied(self):
        """Incomparable is not equal. Treating it as tied would let a
        plan order things it was never given a fact about."""
        assert tier_rules.within_band(None, 1.0) is False
        assert tier_rules.within_band(1.0, None) is False


class TestTheFactRanksFirst:
    def test_a_known_supplier_beats_a_paying_stranger(self):
        """THE RULE, TESTED AT ITS MOST EXPENSIVE POINT. A MAX
        supplier does not outrank somebody this shop already deals
        with."""
        known = _profile(tier="FREE", name="Known Co", ident="known")
        paying = _profile(tier="MAX", name="Paying Co", ident="paying")

        ordered = tie_break.order_untried_suppliers(
            [paying, known], connected_ids={"known"}
        )

        assert [p.id for p in ordered] == ["known", "paying"]

    def test_among_strangers_the_plan_orders_them(self):
        """Two strangers are genuinely indistinguishable from the
        shop's own data. The alphabet was breaking that tie before --
        not a fairer rule, just a blinder one."""
        free = _profile(tier="FREE", name="Aardvark", ident="free")
        pro = _profile(tier="PRO", name="Zebra", ident="pro")

        ordered = tie_break.order_untried_suppliers([free, pro], connected_ids=set())

        assert [p.id for p in ordered] == ["pro", "free"]

    def test_equal_plans_fall_back_to_the_alphabet(self):
        """Deterministic: a rail that reorders between identical
        requests is one nobody can debug."""
        b = _profile(tier="PRO", name="Beta", ident="b")
        a = _profile(tier="PRO", name="Alpha", ident="a")

        ordered = tie_break.order_untried_suppliers([b, a], connected_ids=set())

        assert [p.id for p in ordered] == ["a", "b"]

    def test_an_expired_plan_does_not_win_the_tie(self):
        """The expiry rule reaching the thing it exists to protect."""
        lapsed = _profile(
            tier="MAX", expires=utcnow() - timedelta(days=1), name="Zebra", ident="lapsed"
        )
        free = _profile(tier="FREE", name="Aardvark", ident="free")

        ordered = tie_break.order_untried_suppliers([lapsed, free], connected_ids=set())

        assert [p.id for p in ordered] == ["free", "lapsed"]
