"""
Demand we are failing to meet, counted.

THE CLAIM UNDER TEST: "412 shops tell us they sell soap and not one has
ever bought soap here" is producible from data we already have, without
naming a single shop.

CATEGORIES HERE ARE REAL ProductCategory VALUES, deliberately. An
earlier draft used "AIRTIME_DATA", which passes -- buys_categories is
an array of strings and the rule never looks the value up -- while
testing a category the form cannot produce. A test that only works on
impossible input is a test nobody should trust.

WHY IT IS TESTED WITH REAL ORDERS rather than stubbed counts: the whole
value of this report is that it runs the SAME reconciliation rule the
feed runs. A test that stubbed the counts would pass happily on the day
somebody re-expressed that rule in SQL and the two drifted apart --
which is the exact failure the service was written to avoid.
"""
from __future__ import annotations

import uuid
from itertools import count

import pytest

from src.domains.business.demand.insights.services import gap_service
from src.extensions import db

_seq = count()


@pytest.fixture()
def declaring_shop(make_business):
    """A shop that has said what it buys."""
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    def _make(categories):
        n = next(_seq)
        user = make_business(f"gap{n}@example.com")
        profile = BusinessProfileRepository.get_or_create_for_business(user.id)
        profile.buys_categories = list(categories)
        db.session.commit()
        return user

    return _make


@pytest.fixture()
def buys(db_session):
    """Give a shop one confirmed order in a category."""
    from src.core.base_model import utcnow
    from src.domains.auth.models.user import User, UserRole, VerificationStatus
    from src.domains.catalogue.products.models.taxonomy import ProductUnit
    from src.domains.network.orders.models.stock_order import (
        StockOrder,
        StockOrderItem,
        StockOrderStatus,
    )
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer
    from src.domains.supplier.supplier_profile.models.supplier_profile import (
        SupplierProfile,
        SupplierVerificationStatus,
    )

    def _buy(business_user, category):
        n = next(_seq)
        seller = User(
            id=uuid.uuid4(),
            email=f"gap-seller{n}@example.com",
            password_hash="x",
            role=UserRole.SUPPLIER,
            verification_status=VerificationStatus.VERIFIED,
        )
        db.session.add(seller)
        db.session.flush()
        profile = SupplierProfile(
            supplier_id=seller.id,
            business_name=f"Gap Wholesale {n}",
            verification_status=SupplierVerificationStatus.VERIFIED,
        )
        db.session.add(profile)
        db.session.flush()

        offer = SupplierOffer(
            supplier_profile_id=profile.id,
            name=f"Thing {n}",
            category=category,
            price_cents=1500,
            selling_unit=ProductUnit.EACH,
            sku=f"SKU-GAP-{n}",
            product_code=f"PC-GAP-{n}",
        )
        db.session.add(offer)
        db.session.flush()

        order = StockOrder(
            business_id=business_user.id,
            supplier_profile_id=profile.id,
            status=StockOrderStatus.CONFIRMED,
            submitted_at=utcnow(),
            total_cents=1500,
        )
        db.session.add(order)
        db.session.flush()
        db.session.add(
            StockOrderItem(
                stock_order_id=order.id,
                product_id=offer.id,
                quantity=1,
                price_cents_at_add_time=offer.price_cents,
            )
        )
        db.session.commit()

    return _buy


def _row(report, category):
    return next((r for r in report["categories"] if r["category"] == category), None)


class TestTheNumberThatSellsTheEcosystem:
    def test_shops_that_declare_and_never_buy_are_counted(
        self, app, db_session, declaring_shop
    ):
        for _ in range(3):
            declaring_shop(["PERSONAL_CARE"])

        report = gap_service.unserved_by_category()

        assert _row(report, "PERSONAL_CARE")["shopsUnserved"] == 3

    def test_a_shop_that_buys_the_thing_is_not_a_gap(
        self, app, db_session, declaring_shop, buys
    ):
        """THE HALF THAT MAKES THE NUMBER HONEST. Counting every
        declaration would report a gap for a category we serve
        perfectly well."""
        from src.domains.catalogue.products.models.taxonomy import ProductCategory

        for _ in range(3):
            shop = declaring_shop(["BAKERY"])
            buys(shop, ProductCategory.BAKERY)

        report = gap_service.unserved_by_category(min_shops=1)

        assert _row(report, "BAKERY") is None

    def test_buying_something_else_still_leaves_the_gap(
        self, app, db_session, declaring_shop, buys
    ):
        """They are active customers. They buy their bread elsewhere --
        which is precisely the conversation worth having."""
        from src.domains.catalogue.products.models.taxonomy import ProductCategory

        for _ in range(3):
            shop = declaring_shop(["BAKERY"])
            buys(shop, ProductCategory.HOUSEHOLD_CLEANING)

        report = gap_service.unserved_by_category()

        assert _row(report, "BAKERY")["shopsUnserved"] == 3
        assert _row(report, "BAKERY")["shareUnserved"] == 1.0

    def test_the_biggest_gap_comes_first(self, app, db_session, declaring_shop):
        for _ in range(3):
            declaring_shop(["BAKERY"])
        for _ in range(5):
            declaring_shop(["PERSONAL_CARE"])

        report = gap_service.unserved_by_category()

        assert report["categories"][0]["category"] == "PERSONAL_CARE"

    def test_partial_service_shows_as_a_share(
        self, app, db_session, declaring_shop, buys
    ):
        """A category at 100% is a hole; one at 50% is a supplier who
        cannot keep up, and the two need different responses."""
        from src.domains.catalogue.products.models.taxonomy import ProductCategory

        for _ in range(3):
            declaring_shop(["BAKERY"])
        for _ in range(3):
            shop = declaring_shop(["BAKERY"])
            buys(shop, ProductCategory.BAKERY)

        report = gap_service.unserved_by_category()

        row = _row(report, "BAKERY")
        assert row["shopsDeclaring"] == 6
        assert row["shopsUnserved"] == 3
        assert row["shareUnserved"] == 0.5


class TestItNeverIdentifiesAShop:
    def test_a_category_below_the_threshold_is_withheld(
        self, app, db_session, declaring_shop
    ):
        """AN AGGREGATE OF ONE IS NOT AN AGGREGATE. "1 shop needs
        soap" is a sentence about a person."""
        declaring_shop(["PERSONAL_CARE"])

        report = gap_service.unserved_by_category()

        assert report["categories"] == []

    def test_withholding_is_never_silent(self, app, db_session, declaring_shop):
        """A report that quietly drops small categories reads as "no
        gaps there", which is the opposite of what it means."""
        declaring_shop(["PERSONAL_CARE"])

        report = gap_service.unserved_by_category()

        assert report["suppressed"] == 1

    def test_no_shop_id_appears_anywhere_in_the_report(
        self, app, db_session, declaring_shop
    ):
        """The one property that must hold whatever else changes."""
        shops = [declaring_shop(["PERSONAL_CARE"]) for _ in range(3)]

        report = gap_service.unserved_by_category()

        rendered = repr(report)
        for shop in shops:
            assert str(shop.id) not in rendered

    def test_the_threshold_is_reported_with_the_numbers(
        self, app, db_session, declaring_shop
    ):
        """So nobody reads a lowered-threshold report as a publishable
        one."""
        for _ in range(2):
            declaring_shop(["PERSONAL_CARE"])

        assert gap_service.unserved_by_category(min_shops=1)["minShops"] == 1
        assert gap_service.unserved_by_category()["minShops"] == 3


class TestTheEmptyCases:
    def test_a_platform_where_nobody_declared_anything_reports_nothing(
        self, app, db_session
    ):
        report = gap_service.unserved_by_category()

        assert report["categories"] == []
        assert report["shopsConsidered"] == 0

    def test_a_named_subset_can_be_asked_about(self, app, db_session, declaring_shop):
        """A pilot, a township, one supplier's delivery area later."""
        inside = [declaring_shop(["PERSONAL_CARE"]) for _ in range(2)]
        declaring_shop(["BAKERY"])

        report = gap_service.unserved_for_shops([s.id for s in inside])

        assert report["shopsConsidered"] == 2
        assert [r["category"] for r in report["categories"]] == ["PERSONAL_CARE"]
