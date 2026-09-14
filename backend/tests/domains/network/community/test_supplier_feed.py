"""
The supplier's Community feed.

THE THING THIS REPLACES. Today the supplier's Community is a direct
mirror of the business's -- For You, My Connections, search -- and
V2_04 §3.1 names that as the mistake: a supplier does not shop, so a
rail of other suppliers is symmetry mistaken for design.

  For the business, Community is a MARKET.
  For the supplier, Community is a DEMAND SIGNAL.

WHAT THESE TESTS ACTUALLY DEFEND, in order of how much it would hurt
to get wrong:

  A ZERO CARD IS WORSE THAN NO CARD. A new supplier with nothing must
  see an EMPTY feed, not four rows telling them how little they have.
  Every builder returns None when it has nothing, and
  test_a_brand_new_supplier_sees_nothing is what stops somebody
  "helpfully" returning an empty shell.

  ONE ORDER IS NOT A PATTERN. Flagging a business as overdue after a
  single order would be the platform inventing a rhythm from one
  point, and the supplier would phone somebody who is not late.

  THE GROWTH RAIL EXCLUDES PEOPLE YOU ALREADY KNOW. A "businesses near
  you" list containing your own customers is not a growth surface, it
  is a bug that looks like data.
"""
from __future__ import annotations

from datetime import timedelta
from itertools import count

import pytest

from src.core.base_model import utcnow
from src.domains.network.community.algorithms import distance, reorder_gap
from src.domains.network.community.services import feed_service
from src.domains.network.community.supplier import sections as supplier_sections
from src.extensions import db

_seq = count()


@pytest.fixture()
def supplier(make_supplier, make_supplier_profile):
    def _make(lat=-26.2041, lon=28.0473, **overrides):
        n = next(_seq)
        user = make_supplier(f"feedseller{n}@example.com")
        return make_supplier_profile(
            user,
            business_name=f"Wholesaler {n}",
            collection_latitude=lat,
            collection_longitude=lon,
            **overrides,
        )

    return _make


@pytest.fixture()
def business_at(make_business):
    """A business with a real BusinessProfile and coordinates."""
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    def _make(lat=-26.2050, lon=28.0480, name=None):
        n = next(_seq)
        user = make_business(f"feedbuyer{n}@example.com")
        profile = BusinessProfileRepository.get_or_create_for_business(user.id)
        profile.business_name = name or f"Corner Shop {n}"
        profile.latitude = lat
        profile.longitude = lon
        db.session.commit()
        return user, profile

    return _make


def _section(sections, type_name):
    return next((s for s in sections if s["type"] == type_name), None)


class TestTheEmptyCase:
    def test_a_brand_new_supplier_sees_nothing(self, app, db_session, supplier):
        """A ZERO CARD IS WORSE THAN NO CARD. Four rows of zeroes is the
        platform telling somebody how little they have on the day they
        arrive."""
        profile = supplier()

        sections = feed_service.feed_for(profile.supplier_id, "supplier")

        # Shopfront health is the one exception, and correctly so: a
        # supplier with nothing listed HAS something to act on.
        assert [s["type"] for s in sections] == ["STOREFRONT_HEALTH"]

    def test_a_supplier_with_no_profile_gets_an_empty_feed(
        self, app, db_session, make_user
    ):
        """Not a crash and not a 404 -- a feed before the profile exists
        is simply empty.

        BUILT WITH make_user, NOT make_supplier, and the difference is
        the point: make_supplier seeds a profile because OTP
        verification does (otp_service._seed_supplier_profile), so it
        cannot produce this state. The state is reachable only between
        registration and verification, which is exactly when somebody
        could hit the endpoint with a valid token and no profile.
        """
        from src.domains.auth.models.user import UserRole, VerificationStatus

        user = make_user(
            "noprofile@example.com",
            role=UserRole.SUPPLIER,
            verification_status=VerificationStatus.VERIFIED,
        )
        db.session.commit()

        assert feed_service.feed_for(user.id, "supplier") == []


class TestReorderDue:
    def test_one_order_is_not_a_pattern(self, app, db_session):
        """THE MOST IMPORTANT RULE IN THE ALGORITHM. A business that has
        ordered once is new, not overdue -- calling them overdue would
        invent a rhythm from a single point and send the supplier to
        phone somebody who is not late."""
        now = utcnow()
        pattern = reorder_gap.pattern_from([now - timedelta(days=90)], now)

        assert pattern.order_count == 1
        assert pattern.typical_gap_days is None
        assert pattern.is_overdue is False

    def test_a_weekly_customer_is_overdue_before_a_monthly_one(self, app):
        """OVERDUE IS A RATIO, NOT A DAY COUNT. A fixed threshold would
        spam the supplier about the weekly shopper and never fire for
        the monthly one."""
        now = utcnow()
        weekly = reorder_gap.pattern_from(
            [now - timedelta(days=d) for d in (28, 21, 14, 12)], now
        )
        monthly = reorder_gap.pattern_from(
            [now - timedelta(days=d) for d in (90, 60, 30, 12)], now
        )

        assert weekly.typical_gap_days is not None
        assert monthly.typical_gap_days is not None
        # Same 12 days of silence, opposite verdicts.
        assert weekly.is_overdue is True
        assert monthly.is_overdue is False

    def test_a_customer_ordering_on_time_is_not_flagged(self, app):
        now = utcnow()
        pattern = reorder_gap.pattern_from(
            [now - timedelta(days=d) for d in (21, 14, 7, 1)], now
        )

        assert pattern.typical_gap_days == pytest.approx(6.7, abs=0.5)
        assert pattern.is_overdue is False


class TestBusinessesNearYou:
    def test_it_excludes_businesses_you_already_deal_with(
        self, app, db_session, supplier, business_at, make_active_connection
    ):
        """A GROWTH RAIL CONTAINING YOUR OWN CUSTOMERS is not a growth
        surface -- it is a bug that looks like data."""
        profile = supplier()
        connected_user, _ = business_at(name="Already Mine")
        stranger_user, _ = business_at(name="Not Yet Mine")
        make_active_connection(connected_user, profile)

        section = supplier_sections.businesses_near_you(profile)

        assert section is not None
        names = [b["businessName"] for b in section["businesses"]]
        assert "Not Yet Mine" in names
        assert "Already Mine" not in names

    def test_a_supplier_with_no_location_gets_no_rail(
        self, app, db_session, supplier, business_at
    ):
        """WITHOUT OUR OWN LOCATION THERE IS NO "NEAR". An unsorted list
        of every business would be worse than nothing -- it would look
        like a recommendation."""
        profile = supplier(lat=None, lon=None)
        business_at()

        assert supplier_sections.businesses_near_you(profile) is None

    def test_nearest_first(self, app, db_session, supplier, business_at):
        profile = supplier(lat=-26.2041, lon=28.0473)
        business_at(lat=-26.4000, lon=28.2000, name="Far Shop")
        business_at(lat=-26.2045, lon=28.0475, name="Close Shop")

        section = supplier_sections.businesses_near_you(profile)

        names = [b["businessName"] for b in section["businesses"]]
        assert names.index("Close Shop") < names.index("Far Shop")


class TestShopfrontHealth:
    def test_it_names_the_specific_thing_blocking_them(
        self, app, db_session, supplier
    ):
        """NOT VANITY METRICS. Every item is something a supplier can
        act on in one tap."""
        profile = supplier()

        section = supplier_sections.shopfront_health(profile)

        codes = {i["code"] for i in section["issues"]}
        assert "NO_LIVE_OFFERS" in codes
        assert "NO_MINIMUM_ORDER" in codes

    def test_it_disappears_when_nothing_is_wrong(self, app, db_session, supplier):
        """The card congratulates nobody. It is absent when there is
        nothing to fix."""
        from src.domains.catalogue.products.models.taxonomy import (
            ProductCategory,
            ProductUnit,
        )
        from src.domains.supplier.products.services import product_service

        profile = supplier(minimum_order_cents=5000)
        offer = product_service.create_product(
            supplier_profile_id=profile.id,
            name="Maize Meal 10kg",
            category=ProductCategory.FOOD_GROCERY,
            price_cents=8900,
            selling_unit=ProductUnit.EACH,
        )
        # Matched to the catalogue, so nothing is unmatched either.
        from src.domains.catalogue.products.models.product import Product

        product = Product(
            name="Maize Meal 10kg",
            normalized_name="maize meal 10kg",
            category=ProductCategory.FOOD_GROCERY,
        )
        db.session.add(product)
        db.session.flush()
        offer.product_id = product.id
        db.session.commit()

        assert supplier_sections.shopfront_health(profile) is None


class TestDistance:
    def test_an_unknown_point_is_none_not_a_sentinel(self):
        """A business that has not set a location is not "infinitely far
        away" -- the distance is unknown, and a caller sorting by it has
        to decide what that means rather than being handed a number
        that sorts plausibly and means nothing."""
        assert distance.km_between(None, 28.0, -26.0, 28.0) is None
        assert distance.km_between(-26.0, 28.0, None, None) is None

    def test_it_measures_a_real_distance(self):
        """Johannesburg to Pretoria, roughly 50km."""
        km = distance.km_between(-26.2041, 28.0473, -25.7479, 28.2293)

        assert 45 < km < 60


class TestTheRoleGate:
    def test_the_business_feed_is_real_now(self, app, db_session, make_business):
        """SUPERSEDED. This asserted the business feed returned [] while
        it was unbuilt and the tab was served by a mock. It is built --
        see test_business_feed.py -- so the assertion now defends the
        opposite property: a business with nothing still gets a usable
        tab, never an empty screen."""
        user = make_business("feedbiz@example.com")

        sections = feed_service.feed_for(user.id, "business")

        assert [s["type"] for s in sections] == ["CATEGORY_CHIPS", "PROMO"]

    def test_an_unknown_role_is_refused(self, app, db_session):
        from src.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            feed_service.feed_for("00000000-0000-0000-0000-000000000001", "admin")
