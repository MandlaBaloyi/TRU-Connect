"""
"Can you collect your own stock?" — and the three answers it has.

THE RULE THIS FILE EXISTS TO HOLD, and it is the one Mandla insisted
on before the field was built:

    "we need more viable than hypothesis or assumptions"

An optional question that gets DEFAULTED turns a missing answer into
an invented one, and the feed is then ranking on a hypothesis it
cannot tell apart from a fact. So can_collect is tri-state from the
column to the rail:

    True   they have transport          rail unchanged
    False  they said they cannot        rail withheld
    None   never asked                  rail unchanged

THE WHOLE BUG THIS PREVENTS IS ONE CHARACTER. `if not needs.can_collect`
instead of `if needs.can_collect is False` folds None into False and
withholds the rail from every shop that predates the question -- which
is the invented answer, arriving through a truthiness check rather
than through a default. It would also be invisible: the rail simply
stops appearing, for a reason nobody can see.

It is the same tri-state rule SupplierProfile.offers_delivery already
follows on the other side of the same question.
"""
from __future__ import annotations

from itertools import count

import pytest

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
    @pytest.mark.parametrize("stored", [True, False, None])
    def test_all_three_states_reach_shop_needs_unchanged(self, app, shop, stored):
        """None must arrive as None. If any layer coerces it, the rail
        below cannot tell "said no" from "never asked"."""
        profile = _profile(shop.id)
        profile.buys_categories = ["FOOD_GROCERY"]
        profile.can_collect = stored
        db.session.commit()

        assert needs_service.needs_for(shop.id).can_collect is stored

    def test_a_shop_with_no_profile_row_is_unknown_not_false(self, app, shop):
        """A brand-new account has never been asked, and that is not the
        same as having said no."""
        assert needs_service.needs_for(shop.id).can_collect is None


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

    def test_the_rail_shows_when_they_can_collect(
        self, app, shop, make_supplier, make_supplier_profile
    ):
        from src.domains.network.community.business import sections

        self._near_suppliers(make_supplier, make_supplier_profile, shop)
        _profile(shop.id).can_collect = True
        db.session.commit()

        assert sections.collect_near_you(shop.id) is not None

    def test_the_rail_shows_when_they_have_NOT_been_asked(
        self, app, shop, make_supplier, make_supplier_profile
    ):
        """THE ONE THAT CATCHES THE TRUTHINESS BUG. Every shop that
        existed before this question was added has None here, and every
        one of them must still see the rail."""
        from src.domains.network.community.business import sections

        self._near_suppliers(make_supplier, make_supplier_profile, shop)
        _profile(shop.id).can_collect = None
        db.session.commit()

        assert sections.collect_near_you(shop.id) is not None, (
            "None means 'never asked'. Withholding the rail here would be the "
            "invented answer the tri-state exists to prevent."
        )

    def test_the_rail_is_withheld_when_they_said_they_cannot(
        self, app, shop, make_supplier, make_supplier_profile
    ):
        """A row for collecting is worth nothing to a shop without
        transport -- every card on it is a trip they cannot make."""
        from src.domains.network.community.business import sections

        self._near_suppliers(make_supplier, make_supplier_profile, shop)
        _profile(shop.id).can_collect = False
        db.session.commit()

        assert sections.collect_near_you(shop.id) is None
