"""
Discovery asks what the shop actually buys.

THE HOLE THESE CLOSE. Both discovery rails recommended suppliers
without consulting the demand engine. not_ordered_yet_suppliers took
every visible supplier with stock and let the ALPHABET decide;
collect_near_you sorted by distance and nothing else. A shop buying
food and beauty was shown a supplier selling neither, forever, because
their name began with M.

It was invisible on a seeded catalogue of broad wholesalers who each
carry a bit of everything. In a real market of specialists it is the
obvious failure, and it is the reason these tests build NARROW
suppliers -- one category each -- rather than realistic ones.

WHAT THEY DEFEND, worst consequence first:

  MONEY NEVER OUTRANKS RELEVANCE. tie_break's rule is that the organic
  fact ranks first and tier enters the sort key after it, "the whole
  mechanical difference between a tie-break and an auction". What a
  shop buys is an organic fact, so a PARTNER-tier supplier selling
  nothing they buy must lose to a FREE-tier supplier who stocks it. If
  that ever inverts, the rail is being sold.

  A SHOP WITH NO SIGNAL STILL SEES SUPPLIERS. Relevance must RANK, not
  gate -- except on collect-near-you, where it filters, and there the
  no-signal case must disable the filter entirely. The shop that has
  declared nothing and ordered nothing is exactly who discovery is for.

  COLLECT NEAR YOU IS NEVER REORDERED. It prints the distance it is
  sorted by, so relevance may decide who is ON it and never in what
  order. A list headed "closest to Mankweng" that is not in distance
  order is unrecoverable -- the reader concludes the order was bought,
  and they would be right.
"""
from __future__ import annotations

from itertools import count

import pytest

from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
from src.extensions import db

_seq = count()


@pytest.fixture()
def supplier_selling(make_supplier, make_supplier_profile):
    """A visible supplier carrying exactly the categories named."""
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer

    def _make(name, categories, **overrides):
        n = next(_seq)
        user = make_supplier(f"rel{n}@example.com")
        profile = make_supplier_profile(user, business_name=name, **overrides)
        for category in categories:
            # SHORT SKUs: the column is varchar(20) and a readable
            # "SKU-REL-0-HARDWARE_GENERAL" is twenty-six characters.
            offer_no = next(_seq)
            db.session.add(
                SupplierOffer(
                    supplier_profile_id=profile.id,
                    name=f"{name} {category.value}",
                    category=category,
                    price_cents=1000,
                    selling_unit=ProductUnit.EACH,
                    sku=f"S{offer_no}",
                    product_code=f"P{offer_no}",
                )
            )
        db.session.commit()
        return profile

    return _make


def _declare(business_id, categories):
    """Tell the demand engine what this shop buys."""
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    profile = BusinessProfileRepository.get_or_create_for_business(business_id)
    profile.buys_categories = [c.value for c in categories]
    db.session.commit()


class TestTheUntriedRailRanksByWhatTheShopBuys:
    def _order(self, business_id):
        from src.domains.network.community.services import feed_detail_service

        return [p.business_name for p in feed_detail_service.not_ordered_yet_suppliers(business_id)]

    def test_a_supplier_who_stocks_it_beats_one_who_does_not(
        self, app, db_session, make_business, supplier_selling
    ):
        """THE WHOLE POINT. Alphabetically "Zzz" loses to "Aaa"; by
        relevance it wins, because it sells what this shop buys."""
        business = make_business()
        _declare(business.id, [ProductCategory.FOOD_GROCERY])

        supplier_selling("Aaa Hardware", [ProductCategory.HARDWARE_GENERAL])
        supplier_selling("Zzz Groceries", [ProductCategory.FOOD_GROCERY])

        assert self._order(business.id)[0] == "Zzz Groceries"

    def test_more_of_what_they_buy_ranks_higher(
        self, app, db_session, make_business, supplier_selling
    ):
        """The score is the SUM of the shop's own weights, so a
        supplier covering two of their categories beats one covering
        one. Carrying everything a shop buys is the most useful thing a
        supplier can do for it."""
        business = make_business()
        _declare(business.id, [ProductCategory.FOOD_GROCERY, ProductCategory.BEVERAGES])

        supplier_selling("Aaa Both", [ProductCategory.FOOD_GROCERY, ProductCategory.BEVERAGES])
        supplier_selling("Aab One", [ProductCategory.BEVERAGES])

        assert self._order(business.id)[0] == "Aaa Both"

    def test_money_does_not_outrank_relevance(
        self, app, db_session, make_business, supplier_selling
    ):
        """THE ANTI-AUCTION PROPERTY, and the reason relevance sits
        ABOVE tier in the sort key rather than below it. A PARTNER
        selling nothing this shop buys must lose to a FREE supplier who
        stocks it -- otherwise the rail is for sale."""
        from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierPlanTier

        business = make_business()
        _declare(business.id, [ProductCategory.FOOD_GROCERY])

        supplier_selling(
            "Aaa Paying Irrelevant",
            [ProductCategory.HARDWARE_GENERAL],
            plan_tier=SupplierPlanTier.PARTNER,
        )
        supplier_selling("Zzz Free Relevant", [ProductCategory.FOOD_GROCERY])

        assert self._order(business.id)[0] == "Zzz Free Relevant"

    def test_a_shop_with_no_signal_keeps_the_old_order(
        self, app, db_session, make_business, supplier_selling
    ):
        """RANK, NEVER GATE. A shop that has declared nothing and
        ordered nothing has no relevance to rank by, so it falls back
        to the alphabet -- and still sees everybody. That shop is who
        this rail exists for."""
        business = make_business()

        supplier_selling("Aaa Hardware", [ProductCategory.HARDWARE_GENERAL])
        supplier_selling("Zzz Groceries", [ProductCategory.FOOD_GROCERY])

        order = self._order(business.id)
        assert order == ["Aaa Hardware", "Zzz Groceries"]
        assert len(order) == 2, "nobody is hidden from a shop with no signal"


class TestCollectNearYouFiltersAndNeverReorders:
    def _rail(self, business_id):
        from src.domains.network.community.services import feed_detail_service

        return feed_detail_service.collect_near_you_suppliers(business_id)

    def _shop_at(self, make_business, lat=-26.2041, lon=28.0473):
        from src.domains.business.business_profile.repositories.business_profile_repository import (
            BusinessProfileRepository,
        )

        user = make_business()
        profile = BusinessProfileRepository.get_or_create_for_business(user.id)
        profile.latitude, profile.longitude = lat, lon
        db.session.commit()
        return user

    def test_a_near_supplier_selling_nothing_they_buy_is_dropped(
        self, app, db_session, make_business, supplier_selling
    ):
        """THE PRECEDENT IS THE RAIL'S OWN: it already drops anyone
        beyond MAX_COLLECTION_KM "rather than shown as the best of a bad
        lot". A wholesaler four hundred metres away selling nothing this
        shop buys is the same kind of card -- near, and no use."""
        shop = self._shop_at(make_business)
        _declare(shop.id, [ProductCategory.FOOD_GROCERY])

        for index in range(3):
            supplier_selling(
                f"Grocer {index}",
                [ProductCategory.FOOD_GROCERY],
                collection_latitude=-26.2045 - index * 0.001,
                collection_longitude=28.0475,
            )
        supplier_selling(
            "Car Parts Next Door",
            [ProductCategory.HARDWARE_GENERAL],
            collection_latitude=-26.2042,
            collection_longitude=28.0474,
        )

        names = [p.business_name for _, p in self._rail(shop.id)]
        assert "Car Parts Next Door" not in names
        assert len(names) == 3

    def test_the_survivors_are_still_in_distance_order(
        self, app, db_session, make_business, supplier_selling
    ):
        """RELEVANCE DECIDES WHO IS ON IT, NEVER THE ORDER. This rail
        prints the number it is sorted by; a reader who sees 2.0km above
        1.2km concludes the order was bought, and they would be right."""
        shop = self._shop_at(make_business)
        _declare(shop.id, [ProductCategory.FOOD_GROCERY])

        for index in range(4):
            supplier_selling(
                f"Grocer {3 - index}",  # names deliberately reverse the distances
                [ProductCategory.FOOD_GROCERY],
                collection_latitude=-26.2045 - index * 0.002,
                collection_longitude=28.0475,
            )

        distances = [km for km, _ in self._rail(shop.id)]
        assert distances == sorted(distances)

    def test_a_shop_with_no_signal_is_not_filtered_at_all(
        self, app, db_session, make_business, supplier_selling
    ):
        """VALVE ONE. Nothing declared, nothing ordered -- so there is
        nothing to match on, and a relevance filter would empty the rail
        for precisely the user it exists for."""
        shop = self._shop_at(make_business)

        for index in range(3):
            supplier_selling(
                f"Somebody {index}",
                [ProductCategory.HARDWARE_GENERAL],
                collection_latitude=-26.2045 - index * 0.001,
                collection_longitude=28.0475,
            )

        assert len(self._rail(shop.id)) == 3

    def test_filtering_never_shrinks_the_rail_below_a_rail(
        self, app, db_session, make_business, supplier_selling
    ):
        """VALVE TWO. A rail that vanishes teaches a shopkeeper that
        nobody is near them, which is a worse lie than a loose card. If
        the filter would leave fewer than MIN_ITEMS_PER_RAIL, the
        unfiltered list is kept."""
        from src.domains.network.community.business.sections import MIN_ITEMS_PER_RAIL

        shop = self._shop_at(make_business)
        _declare(shop.id, [ProductCategory.FOOD_GROCERY])

        # One relevant, three not -- filtering would leave a single card.
        supplier_selling(
            "The Only Grocer",
            [ProductCategory.FOOD_GROCERY],
            collection_latitude=-26.2045,
            collection_longitude=28.0475,
        )
        for index in range(3):
            supplier_selling(
                f"Hardware {index}",
                [ProductCategory.HARDWARE_GENERAL],
                collection_latitude=-26.2046 - index * 0.001,
                collection_longitude=28.0475,
            )

        rail = self._rail(shop.id)
        assert len(rail) == 4, "the unfiltered list is kept rather than a one-card rail"
        assert MIN_ITEMS_PER_RAIL == 3
