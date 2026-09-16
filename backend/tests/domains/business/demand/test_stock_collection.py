"""
"How does stock reach you?" -- and the four states that answer has.

THE RULE THIS FILE EXISTS TO HOLD, and it is the one Mandla insisted on
before the field was built:

    "we need more viable than hypothesis or assumptions"

An optional question that gets DEFAULTED turns a missing answer into an
invented one, and the feed is then ranking on a hypothesis it cannot
tell apart from a fact. So stock_collection carries all four states
from the column to the rail:

    COLLECT   they fetch it themselves    rail unchanged
    BOTH      either, depending           rail unchanged
    DELIVERY  it must come to them        rail WITHHELD
    None      never asked                 rail unchanged

IT WAS A NULLABLE BOOLEAN FIRST, and Mandla was right that two answers
is short by one: "maybe they do both, sometimes they allow deliveries,
sometimes they collect themselves". A shop that fetches small top-ups
and has the month's bulk delivered is making a CHOICE, not living with
a constraint, and storing that as "yes, I collect" loses the
difference.

THE BUG THIS PREVENTS IS A SLOPPY COMPARISON. Testing falsiness, or
"not COLLECT", folds None AND BOTH in with DELIVERY -- withholding the
rail from every shop that predates the question plus everyone who
answered honestly that they do both. It would also be invisible: the
rail simply stops appearing, for a reason nobody can see.

It is the same discipline SupplierProfile.offers_delivery already
follows on the other side of the same question.
"""
from __future__ import annotations

from itertools import count

import pytest

from src.domains.business.business_profile.models.business_profile import StockCollection
from src.domains.business.demand.services import needs_service
from src.extensions import db

_seq = count()


@pytest.fixture()
def shop(make_business):
    return make_business(f"collect{next(_seq)}@example.com")


def _profile(user_id):
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    return BusinessProfileRepository.get_or_create_for_business(user_id)


class TestItSurvivesToTheEngine:
    @pytest.mark.parametrize(
        "stored,expected",
        [
            (StockCollection.COLLECT, "COLLECT"),
            (StockCollection.DELIVERY, "DELIVERY"),
            (StockCollection.BOTH, "BOTH"),
            (None, None),
        ],
    )
    def test_all_four_states_reach_shop_needs_unchanged(self, app, shop, stored, expected):
        """None must arrive as None. If any layer coerces it, the rail
        below cannot tell "said delivery" from "never asked"."""
        profile = _profile(shop.id)
        profile.buys_categories = ["FOOD_GROCERY"]
        profile.stock_collection = stored
        db.session.commit()

        assert needs_service.needs_for(shop.id).stock_collection == expected

    def test_a_shop_with_no_profile_row_is_unknown_not_delivery(self, app, shop):
        """A brand-new account has never been asked, and that is not the
        same as having said it needs delivery."""
        assert needs_service.needs_for(shop.id).stock_collection is None


class TestTheRailReadsIt:
    def _near_suppliers(self, make_supplier, make_supplier_profile, shop_user):
        from src.domains.business.business_profile.repositories.business_profile_repository import (
            BusinessProfileRepository,
        )

        profile = BusinessProfileRepository.get_or_create_for_business(shop_user.id)
        profile.latitude, profile.longitude = -23.8890, 29.7350
        profile.buys_categories = ["FOOD_GROCERY"]
        db.session.commit()

        for i in range(4):
            supplier = make_supplier(f"nearcollect{next(_seq)}@example.com")
            make_supplier_profile(
                supplier,
                business_name=f"Near Co {i}",
                collection_latitude=-23.8890 - (i / 500),
                collection_longitude=29.7350,
            )
        db.session.commit()

    @pytest.mark.parametrize(
        "stored",
        [
            pytest.param(StockCollection.COLLECT, id="collects"),
            # BOTH IS THE ONE A LOOSE COMPARISON BREAKS. "not COLLECT"
            # would withhold the rail from somebody who collects half
            # the time, which is most shops.
            pytest.param(StockCollection.BOTH, id="does-both"),
            # AND None IS THE ONE FALSINESS BREAKS. Every shop that
            # predates the question has this.
            pytest.param(None, id="never-asked"),
        ],
    )
    def test_the_rail_shows_for_everyone_except_delivery_only(
        self, app, shop, make_supplier, make_supplier_profile, stored
    ):
        from src.domains.network.community.business import sections

        self._near_suppliers(make_supplier, make_supplier_profile, shop)
        _profile(shop.id).stock_collection = stored
        db.session.commit()

        assert sections.collect_near_you(shop.id) is not None, (
            f"{stored} must not withhold the rail -- only DELIVERY does. Anything "
            "looser is the invented answer this column exists to prevent."
        )

    def test_the_rail_is_withheld_only_for_delivery(
        self, app, shop, make_supplier, make_supplier_profile
    ):
        """A row for collecting is worth nothing to a shop without
        transport -- every card on it is a trip they cannot make."""
        from src.domains.network.community.business import sections

        self._near_suppliers(make_supplier, make_supplier_profile, shop)
        _profile(shop.id).stock_collection = StockCollection.DELIVERY
        db.session.commit()

        assert sections.collect_near_you(shop.id) is None
