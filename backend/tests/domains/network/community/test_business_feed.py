"""
The business's Community feed.

FOR THE BUSINESS, COMMUNITY IS A MARKET -- the mirror of
test_supplier_feed.py, which defends the same tab as a DEMAND SIGNAL.

WHAT THESE DEFEND, in order of how much it would hurt to get wrong:

  AN UNVERIFIED SUPPLIER MUST NOT APPEAR. The curtain (V2_12) makes an
  unverified supplier unfindable, and a discovery rail is precisely
  where a bypass would hide -- nobody notices an EXTRA card. This is the
  one failure here with a real-world victim: a business ordering from
  somebody the platform has not checked.

  A NEW BUSINESS MUST NOT SEE AN EMPTY SCREEN. Categories are the one
  section that is never personal and never absent, so the tab works on
  day one. Everything else fills as they trade.

  A THIN RAIL IS WORSE THAN NO RAIL. Same rule as the supplier feed and
  as the app's own MIN_ITEMS_PER_RAIL -- two cards under a heading looks
  broken in a way zero cards does not.

  A DISCOVERY RAIL MUST NOT CONTAIN YOUR OWN SUPPLIERS. "Collect near
  you" listing the wholesaler you buy from weekly is not discovery, it
  is a bug that looks like data -- the same mistake businesses_near_you
  guards against from the supplier's side.
"""
from __future__ import annotations

from itertools import count

import pytest

from src.domains.network.community.business import sections as business_sections
from src.domains.network.community.services import feed_service
from src.extensions import db

_seq = count()


@pytest.fixture()
def business_at(make_business):
    """A business with a real profile and coordinates."""
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    def _make(lat=-26.2041, lon=28.0473, city="Soweto"):
        n = next(_seq)
        user = make_business(f"feedbuyer{n}@example.com")
        profile = BusinessProfileRepository.get_or_create_for_business(user.id)
        profile.latitude = lat
        profile.longitude = lon
        profile.city_or_town = city
        db.session.commit()
        return user, profile

    return _make


@pytest.fixture()
def supplier_at(make_supplier, make_supplier_profile):
    def _make(lat=-26.2050, lon=28.0480, name=None, **overrides):
        n = next(_seq)
        user = make_supplier(f"feedseller{n}@example.com")
        return make_supplier_profile(
            user,
            business_name=name or f"Wholesaler {n}",
            collection_latitude=lat,
            collection_longitude=lon,
            **overrides,
        )

    return _make


def _section(sections, type_name):
    return next((s for s in sections if s["type"] == type_name), None)


class TestTheCurtainHolds:
    def test_an_unverified_supplier_is_not_in_collect_near_you(
        self, app, db_session, business_at, supplier_at
    ):
        """THE ONE FAILURE HERE WITH A VICTIM. Nobody notices an extra
        card, which is exactly why this is a test and not a code
        review."""
        from src.domains.supplier.supplier_profile.models.supplier_profile import (
            SupplierVerificationStatus,
        )

        user, _ = business_at()
        for _ in range(3):
            supplier_at()
        hidden = supplier_at(name="Not Checked Yet")
        hidden.verification_status = SupplierVerificationStatus.UNVERIFIED
        db.session.commit()

        section = business_sections.collect_near_you(user.id)

        assert section is not None
        names = [s["businessName"] for s in section["suppliers"]]
        assert "Not Checked Yet" not in names


class TestADiscoveryRailIsForDiscovery:
    def test_collect_near_you_includes_your_own_suppliers_badged(
        self, app, db_session, business_at, supplier_at, make_active_connection
    ):
        """REVERSED DELIBERATELY. An earlier version excluded connected
        suppliers, on the reasoning that a discovery rail containing
        your own suppliers is a bug. That is right for a rail called
        "new near you" and wrong for one called "COLLECT near you":
        proximity is useful whoever they are, and the wholesaler you
        already buy from being nearest is information, not noise.

        They are BADGED rather than hidden -- the card has always had an
        isConnected flag and nothing ever set it."""
        user, _ = business_at()
        mine = supplier_at(name="Already Mine")
        for _ in range(3):
            supplier_at()
        make_active_connection(user, mine)

        section = business_sections.collect_near_you(user.id)

        assert section is not None
        by_name = {s["businessName"]: s for s in section["suppliers"]}
        assert "Already Mine" in by_name, "a supplier you buy from is still nearby"
        assert by_name["Already Mine"]["isConnected"] is True
        assert all(
            s["isConnected"] is False for n, s in by_name.items() if n != "Already Mine"
        )

    def test_no_coordinates_means_no_rail(self, app, db_session, business_at, supplier_at):
        """WITHOUT OUR OWN LOCATION THERE IS NO "NEAR", and an unsorted
        list of every supplier would look like a recommendation."""
        user, _ = business_at(lat=None, lon=None)
        for _ in range(3):
            supplier_at()

        assert business_sections.collect_near_you(user.id) is None

    def test_nearest_first(self, app, db_session, business_at, supplier_at):
        """ALL THREE ARE INSIDE MAX_COLLECTION_KM on purpose. They used
        to be 50km and 110km out, which tested ordering perfectly well
        right up until the rail gained the ceiling it should always have
        had -- at which point two of them vanished and this read as a
        regression instead of the fix it was."""
        user, _ = business_at(lat=-26.2041, lon=28.0473)
        supplier_at(lat=-26.3500, lon=28.1500, name="Far")      # ~19km
        supplier_at(lat=-26.2045, lon=28.0475, name="Close")    # ~50m
        supplier_at(lat=-26.2500, lon=28.0900, name="Middle")   # ~7km

        section = business_sections.collect_near_you(user.id)

        names = [s["businessName"] for s in section["suppliers"]]
        assert names.index("Close") < names.index("Middle") < names.index("Far")

    def test_a_supplier_beyond_the_radius_is_dropped_not_ranked_last(
        self, app, db_session, business_at, supplier_at
    ):
        """THE BUG MANDLA FOUND, and it is a lie rather than a mistake:
        the rail sorted by distance and took the nearest N with NO
        ceiling, so on a thin platform a supplier 328km away appeared
        under a heading that says "near you" purely because nothing
        closer existed.

        SORTING IS NOT FILTERING. The nearest of a distant set is still
        distant, and nobody collects stock from another province.
        """
        user, _ = business_at(lat=-26.2041, lon=28.0473)
        supplier_at(lat=-26.2045, lon=28.0475, name="Close")
        supplier_at(lat=-26.2100, lon=28.0500, name="AlsoClose")
        supplier_at(lat=-26.2200, lon=28.0600, name="StillClose")
        supplier_at(lat=-23.8900, lon=29.7300, name="AnotherProvince")

        section = business_sections.collect_near_you(user.id)

        names = [s["businessName"] for s in section["suppliers"]]
        assert "AnotherProvince" not in names
        assert len(names) == 3

    def test_the_rail_vanishes_when_nobody_is_actually_near(
        self, app, db_session, business_at, supplier_at
    ):
        """AND THAT IS THE HONEST ANSWER. A shop with no supplier in
        range should see no rail, not a rail full of distant ones --
        which is also what makes the rail RESPOND when somebody moves
        their pin, the behaviour that made the bug visible."""
        user, _ = business_at(lat=-26.2041, lon=28.0473)
        for i in range(4):
            supplier_at(lat=-23.8900 + (i / 100), lon=29.7300, name=f"FarAway{i}")

        assert business_sections.collect_near_you(user.id) is None

    def test_a_thin_rail_does_not_appear_at_all(self, app, db_session, business_at, supplier_at):
        """Two cards under a heading looks broken in a way zero cards
        does not."""
        user, _ = business_at()
        supplier_at()
        supplier_at()

        assert business_sections.collect_near_you(user.id) is None


class TestTheNewBusiness:
    def test_a_brand_new_business_still_gets_a_usable_tab(
        self, app, db_session, make_business
    ):
        """No orders, no connections, no location -- and the tab must
        still work.

        TWO SECTIONS, AND BOTH EARN THEIR PLACE. Categories are how you
        shop before you have anything; the prompt is the one thing that
        can make the NEXT visit better, and without it the demand engine
        would sit waiting for a declaration nobody was invited to
        make."""
        user = make_business("brandnew@example.com")

        sections = feed_service.feed_for(user.id, "business")

        assert [s["type"] for s in sections] == ["CATEGORY_CHIPS", "PROMO"]
        assert len(sections[0]["categories"]) == 17
        assert sections[1]["id"] == "tell-us-what-you-buy"

    def test_buy_it_again_carries_the_supplier_on_every_card(
        self, app, db_session, business_at, supplier_at
    ):
        """THE HIGHEST-VALUE RAIL, and the happy path is worth a real
        order rather than a mock: a feed rail MIXES suppliers where a
        shopfront never does, so every card has to name whose it is.
        Getting that wrong means a shopkeeper taps "buy again" and lands
        in the wrong shop."""
        from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )
        from src.domains.supplier.products.models.supplier_offer import SupplierOffer
        from src.core.base_model import utcnow

        user, _ = business_at()
        supplier = supplier_at(name="Bread Wholesale")

        offers = []
        for i, name in enumerate(["White Bread", "Brown Bread", "Rolls"]):
            offer = SupplierOffer(
                supplier_profile_id=supplier.id,
                name=name,
                category=ProductCategory.BAKERY,
                price_cents=1500 + i,
                selling_unit=ProductUnit.EACH,
                sku=f"SKU-BIA-{i}",
                product_code=f"PC-BIA-{i}",
            )
            db.session.add(offer)
            offers.append(offer)
        db.session.flush()

        order = StockOrder(
            business_id=user.id,
            supplier_profile_id=supplier.id,
            status=StockOrderStatus.CONFIRMED,
            submitted_at=utcnow(),
        )
        db.session.add(order)
        db.session.flush()
        for offer in offers:
            db.session.add(
                StockOrderItem(
                    stock_order_id=order.id,
                    product_id=offer.id,
                    quantity=2,
                    price_cents_at_add_time=offer.price_cents,
                )
            )
        db.session.commit()

        section = business_sections.buy_it_again(user.id)

        assert section is not None
        assert section["type"] == "PRODUCT_RAIL"
        assert len(section["products"]) == 3
        for product in section["products"]:
            assert product["supplierName"] == "Bread Wholesale"
            assert product["supplierId"] == str(supplier.id)
            assert product["unitLabel"]

    def test_buy_it_again_is_absent_rather_than_empty(
        self, app, db_session, make_business
    ):
        user = make_business("noorders@example.com")

        assert business_sections.buy_it_again(user.id) is None


class TestCategoryChips:
    def test_every_category_has_a_label_and_an_icon(self, app):
        """A chip with no icon renders a hole. The app has its own map
        as a fallback, but a missing entry here would silently ship the
        raw enum value as a label."""
        section = business_sections.category_chips()

        assert len(section["categories"]) == 17
        for chip in section["categories"]:
            assert chip["label"] and chip["label"] != chip["value"]
            assert chip["icon"]

    def test_beauty_and_hair_is_present(self, app):
        """Added to the enum on 2026-09-13; the app went a day without
        it. This is the check that would have caught that."""
        values = [c["value"] for c in business_sections.category_chips()["categories"]]

        assert "BEAUTY_HAIR" in values


class TestYourSuppliers:
    def test_connections_appear_as_avatars(
        self, app, db_session, business_at, supplier_at, make_active_connection
    ):
        user, _ = business_at()
        mine = supplier_at(name="My Wholesaler")
        make_active_connection(user, mine)

        section = business_sections.your_suppliers(user.id)

        assert section is not None
        assert section["type"] == "SUPPLIER_AVATARS"
        assert [s["businessName"] for s in section["suppliers"]] == ["My Wholesaler"]

    def test_a_revoked_supplier_drops_off_the_avatars(
        self, app, db_session, business_at, supplier_at, make_active_connection
    ):
        """The curtain covers DISCOVERY. A revoked supplier stops being
        surfaced here even though the connection itself survives -- and
        the order history it produced is untouched, which is V2_12's
        whole distinction.

        REVOCATION IS "BACK TO UNVERIFIED", NOT A FOURTH STATUS -- see
        verification_service.revoke's own docstring. An earlier version
        of this test invented SupplierVerificationStatus.REVOKED, which
        does not exist; going through the real service instead means the
        test cannot drift from what revocation actually does.
        """
        user, _ = business_at()
        supplier = supplier_at(name="Revoked Later")
        make_active_connection(user, supplier)

        assert business_sections.your_suppliers(user.id) is not None

        from src.domains.verification.services import verification_service

        verification_service.revoke(
            supplier.supplier_id,
            decided_by_user_id=str(supplier.supplier_id),
            reason="Documents withdrawn",
        )
        db.session.commit()

        assert business_sections.your_suppliers(user.id) is None

class TestSuppliersYouHaveNotOrderedFrom:
    """THE SECTION THAT WAS CONNECTION-ONLY AND SHOULD NOT HAVE BEEN.

    A connection that stalled after the handshake and a supplier they
    have never met are the SAME opportunity: somebody with stock, in
    reach, never bought from. Restricting it to connections meant a new
    business -- who has none -- saw nothing at all, which is the old
    pre-V2_00-2.3 model leaking back into a discovery rail.
    """

    def _with_stock(self, supplier_at, name):
        from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
        from src.domains.supplier.products.models.supplier_offer import SupplierOffer

        profile = supplier_at(name=name)
        n = next(_seq)
        db.session.add(
            SupplierOffer(
                supplier_profile_id=profile.id,
                name=f"Stock {n}",
                category=ProductCategory.BEVERAGES,
                price_cents=1500,
                selling_unit=ProductUnit.EACH,
                sku=f"SKU-NOY-{n}",
                product_code=f"PC-NOY-{n}",
            )
        )
        db.session.commit()
        return profile

    def test_it_includes_suppliers_you_have_never_connected_to(
        self, app, db_session, business_at, supplier_at
    ):
        user, _ = business_at()
        for i in range(3):
            self._with_stock(supplier_at, f"Stranger {i}")

        section = business_sections.not_ordered_from_yet(user.id)

        assert section is not None
        assert len(section["suppliers"]) == 3

    def test_the_ones_you_already_know_come_first(
        self, app, db_session, business_at, supplier_at, make_active_connection
    ):
        """The trust is done; only the first order is missing, which
        makes it the cheapest one in the app to win."""
        user, _ = business_at()
        for i in range(3):
            self._with_stock(supplier_at, f"Stranger {i}")
        known = self._with_stock(supplier_at, "Connected Already")
        make_active_connection(user, known)

        section = business_sections.not_ordered_from_yet(user.id)

        assert section["suppliers"][0]["businessName"] == "Connected Already"
        assert section["suppliers"][0]["isConnected"] is True

    def test_a_supplier_with_an_empty_shopfront_is_not_an_opportunity(
        self, app, db_session, business_at, supplier_at
    ):
        """Sending a shopkeeper to a blank screen teaches them the rail
        is not worth tapping -- and the ordering gate refuses an empty
        catalogue anyway, so the card could never have become an
        order."""
        user, _ = business_at()
        for i in range(3):
            self._with_stock(supplier_at, f"Has Stock {i}")
        supplier_at(name="Sells Nothing")

        section = business_sections.not_ordered_from_yet(user.id)

        names = [s["businessName"] for s in section["suppliers"]]
        assert "Sells Nothing" not in names


class TestPickUpWhereYouLeftOff:
    """THE RAIL THAT MAKES IMPRESSIONS MEAN SOMETHING.

    Before it existed the impressions table recorded every card the
    feed sent and every card the shop tapped, and the feed looked
    identical either way. The first person to test it opened the tab
    nine times, tapped five cards, saw no difference, and said the
    logic did not add up. It didn't -- a measurement nothing reads is
    bookkeeping.

    WHAT THESE DEFEND, worst consequence first:

      IT IS BUILT FROM TAPS, NOT DELIVERIES. A delivered card was sent;
      a tapped card was CHOSEN. Ranking on deliveries would build a
      rail out of whatever the feed already shows most often -- a rail
      recommending itself, which is how every "recently viewed"
      feature fails.

      IT EMPTIES ITSELF. The moment an order is confirmed the product
      belongs to "Buy it again" and must leave here. A rail that keeps
      nagging after the thing was bought is working against its own
      purpose.

      ONE SUPPLIER CANNOT TAKE THE ROW. Unlike buy-it-again, which is
      exempt because it is the shop's own confirmed history, this is a
      suggestion -- so the anti-domination ceiling applies.
    """

    def _offer(self, supplier_at, *, profile=None, name=None):
        from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
        from src.domains.supplier.products.models.supplier_offer import SupplierOffer

        profile = profile or supplier_at(name=name)
        n = next(_seq)
        offer = SupplierOffer(
            supplier_profile_id=profile.id,
            name=f"Left off {n}",
            category=ProductCategory.BEVERAGES,
            price_cents=1500,
            selling_unit=ProductUnit.EACH,
            sku=f"SKU-LO-{n}",
            product_code=f"PC-LO-{n}",
        )
        db.session.add(offer)
        db.session.commit()
        return profile, offer

    def _tap(self, business_id, offer, *, rail="moving-fast", position=0, days_ago=0):
        from datetime import date, timedelta

        from src.domains.network.impressions.models.feed_impression import (
            ImpressionItemType,
        )
        from src.domains.network.impressions.repositories.impression_repository import (
            ImpressionRepository,
            ImpressionRow,
        )

        row = ImpressionRow(
            rail=rail,
            position=position,
            item_id=str(offer.id),
            item_type=ImpressionItemType.PRODUCT,
            supplier_profile_id=offer.supplier_profile_id,
        )
        on = date.today() - timedelta(days=days_ago)
        ImpressionRepository.bump(business_id, [row], column="delivered", on=on)
        ImpressionRepository.bump(business_id, [row], column="tapped", on=on)

    def _rail(self, business_id):
        from src.domains.network.community.business import sections

        return sections.picked_up_where_you_left(business_id)

    def test_three_tapped_products_make_a_rail(
        self, app, db_session, business_at, supplier_at
    ):
        business, _ = business_at()
        for index in range(3):
            _, offer = self._offer(supplier_at)
            self._tap(business.id, offer, position=index)

        rail = self._rail(business.id)

        assert rail is not None
        assert rail["id"] == "left-off"
        assert len(rail["products"]) == 3

    def test_a_card_that_was_only_delivered_is_not_in_it(
        self, app, db_session, business_at, supplier_at
    ):
        """DELIVERED IS NOT CHOSEN. Three products the feed showed and
        the shop ignored are the opposite of unfinished business."""
        from src.domains.network.impressions.models.feed_impression import (
            ImpressionItemType,
        )
        from src.domains.network.impressions.repositories.impression_repository import (
            ImpressionRepository,
            ImpressionRow,
        )

        business, _ = business_at()
        for index in range(3):
            _, offer = self._offer(supplier_at)
            ImpressionRepository.bump(
                business.id,
                [
                    ImpressionRow(
                        rail="moving-fast",
                        position=index,
                        item_id=str(offer.id),
                        item_type=ImpressionItemType.PRODUCT,
                    )
                ],
                column="delivered",
            )

        assert self._rail(business.id) is None

    def test_a_thin_rail_does_not_appear_at_all(
        self, app, db_session, business_at, supplier_at
    ):
        """Two is not a rail, here as everywhere else in this file."""
        business, _ = business_at()
        for index in range(2):
            _, offer = self._offer(supplier_at)
            self._tap(business.id, offer, position=index)

        assert self._rail(business.id) is None

    def test_a_tap_older_than_the_window_is_forgotten(
        self, app, db_session, business_at, supplier_at
    ):
        """FOURTEEN DAYS. Something glanced at last month is not a
        decision still being made -- it is one already made against."""
        from src.domains.network.community.business.sections import LEFT_OFF_WINDOW_DAYS

        business, _ = business_at()
        for index in range(3):
            _, offer = self._offer(supplier_at)
            self._tap(
                business.id, offer, position=index, days_ago=LEFT_OFF_WINDOW_DAYS + 1
            )

        assert self._rail(business.id) is None

    def test_one_supplier_cannot_take_the_whole_rail(
        self, app, db_session, business_at, supplier_at
    ):
        """THE CEILING APPLIES HERE AND NOT TO buy-it-again, and the
        difference is the whole distinction between remembering and
        recommending. A shop buying fifteen things from one wholesaler
        is a fact about its trading; a wholesaler whose cards happen to
        get opened often is not entitled to the row."""
        from src.domains.network.community.business.sections import MAX_CARDS_PER_SUPPLIER

        business, _ = business_at()
        profile = supplier_at(name="Loud Wholesaler")
        for index in range(MAX_CARDS_PER_SUPPLIER + 3):
            _, offer = self._offer(supplier_at, profile=profile)
            self._tap(business.id, offer, position=index)

        rail = self._rail(business.id)

        assert rail is not None
        assert len(rail["products"]) <= MAX_CARDS_PER_SUPPLIER

    def test_it_carries_no_see_all_arrow(
        self, app, db_session, business_at, supplier_at
    ):
        """There is no screen behind it yet, and _rail_tail's own
        docstring is explicit that an arrow leading nowhere is worse
        than no arrow."""
        business, _ = business_at()
        for index in range(3):
            _, offer = self._offer(supplier_at)
            self._tap(business.id, offer, position=index)

        rail = self._rail(business.id)

        assert "hasMore" not in rail
