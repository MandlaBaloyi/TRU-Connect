"""
The demand engine, Phase 0: declared only.

THE THESIS BEING PROVEN HERE is that DECLARATION BEATS COLD START. A
shop that answers three quick questions should get a useful feed the
same day, months before order history could say anything -- and that
claim is worth a test because if it fails, asking the questions at all
is a waste of a shopkeeper's time.

WHAT THESE DEFEND, worst consequence first:

  UNKNOWN IS NOT EMPTY. A shop that has told us nothing must produce
  zero confidence and no needs, so the feed falls back to platform-wide
  sections. Returning a confident empty answer would silently hide
  every personalised rail from exactly the people who need the fallback.

  "WHEN I RUN OUT" HAS NO CADENCE. IRREGULAR must not become a number.
  Inventing 30 days there makes the feed confidently wrong about
  timing, which is the one kind of wrong that sends somebody a nudge on
  the wrong day.

  UNSAID IS NOT "NO". prefers_bulk must be None, never False, when a
  shop has not answered -- defaulting a tri-state to one of its answers
  is a mistake this codebase already records making once with
  offers_delivery.

  NO SUPPLIER MAY OWN A RAIL. The cap is what stops a wholesaler with
  four hundred products filling the screen, and it is the visible half
  of the anti-domination property the whole demand-first design exists
  for.
"""
from __future__ import annotations

from itertools import count

import pytest

from src.domains.business.demand.algorithms import weighting
from src.domains.business.demand.services import needs_service
from src.domains.network.community.business import sections
from src.extensions import db

_seq = count()


@pytest.fixture()
def shop(make_business):
    """A business whose profile says what it buys."""
    from src.domains.business.business_profile.models.business_profile import (
        RestockRhythm,
        WeeklySpendBand,
    )
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    def _make(categories=None, rhythm=None, spend=None, customer_types=None):
        n = next(_seq)
        user = make_business(f"demand{n}@example.com")
        profile = BusinessProfileRepository.get_or_create_for_business(user.id)
        profile.buys_categories = list(categories or [])
        profile.customer_types = list(customer_types or [])
        profile.restock_rhythm = RestockRhythm(rhythm) if rhythm else None
        profile.weekly_spend_band = WeeklySpendBand(spend) if spend else None
        db.session.commit()
        return user

    return _make


class TestUnknownIsNotEmpty:
    def test_a_shop_that_declared_nothing_has_zero_confidence(self, app, db_session, shop):
        """The feed must be able to tell "we know nothing" from "we know
        they need nothing" -- the first falls back to platform-wide
        sections, the second would hide them."""
        user = shop()

        needs = needs_service.needs_for(user.id)

        assert needs.is_known is False
        assert needs.confidence == 0.0
        assert needs.categories == []

    def test_a_business_with_no_profile_row_does_not_raise(self, app, db_session, make_business):
        """The profile row is created lazily, so a business that has
        never opened the screen has none. An engine that threw here
        would make the feed depend on the form, which is backwards."""
        user = make_business("noprofile-demand@example.com")

        needs = needs_service.needs_for(user.id)

        assert needs.is_known is False


class TestDeclarationBeatsColdStart:
    def test_three_answers_produce_a_usable_model(self, app, db_session, shop):
        """MINUTE ONE, not month three."""
        user = shop(
            categories=["BAKERY", "BEVERAGES"],
            rhythm="TWICE_WEEKLY",
            spend="R500_TO_2000",
            customer_types=["INDIVIDUALS"],
        )

        needs = needs_service.needs_for(user.id)

        assert needs.is_known
        assert set(needs.category_values) == {"BAKERY", "BEVERAGES"}
        assert needs.cadence_days == 3.5
        assert needs.order_ceiling_cents == 150_000
        assert needs.prefers_bulk is False
        assert needs.confidence == 0.8

    def test_every_need_says_where_it_came_from(self, app, db_session, shop):
        """PROVENANCE IS NOT DECORATION. A feed that cannot say "because
        you told us" versus "because you have bought it nine times"
        cannot explain itself, and an unexplainable feed is one nobody
        dares change."""
        user = shop(categories=["BAKERY"])

        needs = needs_service.needs_for(user.id)

        assert needs.categories[0].source == "declared"
        assert needs.categories[0].confidence == weighting.DECLARED_CONFIDENCE

    def test_declaring_more_does_not_rank_them(self, app, db_session, shop):
        """A form with chips has no first choice -- the order on screen
        is alphabetical. Treating the top chip as most important would
        turn a layout accident into a recommendation."""
        user = shop(categories=["BAKERY", "BEVERAGES", "MEAT_FROZEN"])

        weights = {c.weight for c in needs_service.needs_for(user.id).categories}

        assert weights == {1.0}


class TestTheCarefulNulls:
    def test_when_i_run_out_has_no_cadence(self):
        """IRREGULAR is a real answer, not a refusal, and it must not
        become a number."""
        assert weighting.cadence_days("IRREGULAR") is None

    def test_unsaid_customers_is_unknown_not_walk_ins(self):
        assert weighting.prefers_bulk([]) is None
        assert weighting.prefers_bulk(["INDIVIDUALS"]) is False
        assert weighting.prefers_bulk(["OTHER_BUSINESSES"]) is True

    def test_the_top_spend_band_has_no_ceiling(self):
        """A ceiling there would hide the largest orders from the shops
        most able to place them."""
        assert weighting.order_ceiling_cents("OVER_10000") is None


class TestNoSupplierOwnsARail:
    def test_the_cap_keeps_the_rail_a_market(self):
        """A wholesaler with four hundred products would otherwise fill
        it entirely -- their catalogue is simply bigger, and "more
        matches" is not "better for this shop".

        Tested on plain dicts: the rule is a pure function and deserves
        pinning as one."""
        products = [{"supplierId": "big", "id": f"p{i}"} for i in range(10)]
        products += [{"supplierId": "small", "id": "s1"}]

        kept = sections._cap_per_supplier(products, sections.MAX_CARDS_PER_SUPPLIER)

        assert len([p for p in kept if p["supplierId"] == "big"]) == 3
        assert len([p for p in kept if p["supplierId"] == "small"]) == 1

    def test_it_preserves_order(self):
        """Whatever ranking produced the list survives; the cap only
        removes a supplier's fourth card onwards."""
        products = [
            {"supplierId": "a", "id": "1"},
            {"supplierId": "b", "id": "2"},
            {"supplierId": "a", "id": "3"},
        ]

        kept = sections._cap_per_supplier(products, 3)

        assert [p["id"] for p in kept] == ["1", "2", "3"]


class TestTheRailItself:
    def test_no_declaration_means_no_rail_at_all(self, app, db_session, shop):
        """Not an empty heading -- a shop that has told us nothing
        should see the platform-wide sections instead."""
        user = shop()

        assert sections.stock_for_what_you_buy(user.id) is None


class TestAskingForTheDeclaration:
    """WITHOUT THE ASK, PHASE 0 IS INERT. The engine is fed by a form
    and nothing invited anybody to fill it in."""

    def test_it_appears_when_nothing_is_declared(self, app, db_session, shop):
        user = shop()

        promo = sections.tell_us_what_you_buy(user.id)

        assert promo is not None
        assert promo["type"] == "PROMO"
        # SAYS WHAT IT WILL CHANGE. "Complete your profile!" is a chore
        # with no stated benefit -- the pattern every user has learned
        # to dismiss.
        assert "stock" in promo["promo"]["body"].lower()

    def test_it_disappears_once_answered(self, app, db_session, shop):
        user = shop(categories=["BAKERY"])

        assert sections.tell_us_what_you_buy(user.id) is None

    def test_its_destination_is_one_the_app_will_accept(self, app, db_session, shop):
        """PromoCard refuses any href that does not start with
        /business/ rather than navigating somewhere a server told it
        to. A promo the app silently will not open is worse than none,
        because it looks tappable."""
        user = shop()

        href = sections.tell_us_what_you_buy(user.id)["promo"]["href"]

        assert href.startswith("/business/")

    def test_it_asks_for_ONE_thing(self, app, db_session, shop):
        """It does NOT ask for restock rhythm or spend band, even though
        the engine reads both -- nothing visible uses them in Phase 0,
        and asking for what changes nothing is the rule this section
        exists to keep."""
        user = shop()

        body = sections.tell_us_what_you_buy(user.id)["promo"]["body"].lower()

        assert "restock" not in body
        assert "spend" not in body
