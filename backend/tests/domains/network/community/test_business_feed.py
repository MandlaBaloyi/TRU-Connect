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

from src.domains.network.community.services import business_sections, feed_service
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
    def test_it_excludes_suppliers_you_already_buy_from(
        self, app, db_session, business_at, supplier_at, make_active_connection
    ):
        user, _ = business_at()
        mine = supplier_at(name="Already Mine")
        for _ in range(3):
            supplier_at()
        make_active_connection(user, mine)

        section = business_sections.collect_near_you(user.id)

        assert section is not None
        assert "Already Mine" not in [s["businessName"] for s in section["suppliers"]]

    def test_no_coordinates_means_no_rail(self, app, db_session, business_at, supplier_at):
        """WITHOUT OUR OWN LOCATION THERE IS NO "NEAR", and an unsorted
        list of every supplier would look like a recommendation."""
        user, _ = business_at(lat=None, lon=None)
        for _ in range(3):
            supplier_at()

        assert business_sections.collect_near_you(user.id) is None

    def test_nearest_first(self, app, db_session, business_at, supplier_at):
        user, _ = business_at(lat=-26.2041, lon=28.0473)
        supplier_at(lat=-26.9000, lon=28.9000, name="Far")
        supplier_at(lat=-26.2045, lon=28.0475, name="Close")
        supplier_at(lat=-26.5000, lon=28.4000, name="Middle")

        section = business_sections.collect_near_you(user.id)

        names = [s["businessName"] for s in section["suppliers"]]
        assert names.index("Close") < names.index("Middle") < names.index("Far")

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
        still work. Categories are how you shop before you have
        anything."""
        user = make_business("brandnew@example.com")

        sections = feed_service.feed_for(user.id, "business")

        assert [s["type"] for s in sections] == ["CATEGORY_CHIPS"]
        assert len(sections[0]["categories"]) == 17

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
