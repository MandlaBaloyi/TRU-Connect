"""
Browsing suppliers by what they ARE.

WHAT THESE DEFEND, worst consequence first:

  THE NAME DECIDES NOTHING. This screen exists because a business wants
  wholesalers, and matching the business NAME is wrong in both
  directions at once -- it misses "Seshego Cash & Carry" and admits
  "Wholesale Beauty Supplies", who has done nothing wrong. A screen
  anybody can enter by renaming their business is a keyword search
  wearing a filter's clothes.

  THE CURTAIN APPLIES. This is the most discovery-shaped surface in the
  app, so an unverified supplier does not appear, full stop.

  AN EMPTY CATALOGUE IS NOT A RESULT. ordering_gate already refuses an
  order from a supplier with no products; listing them here would be
  offering a door known to be locked.

  A CHIP THAT RETURNS NOTHING IS NEVER DRAWN. The filters are built
  from what actually exists, because an empty result from a chip the
  app drew itself reads as broken.
"""
from __future__ import annotations

from itertools import count

import pytest

from src.domains.network.community.explore.services import explore_service
from src.domains.supplier.supplier_profile.models.supplier_profile import (
    SupplierKind,
    SupplierPlanTier,
    SupplierVerificationStatus,
)
from src.extensions import db

_seq = count()


@pytest.fixture()
def supplier_of(make_supplier, make_supplier_profile):
    """A supplier of a given kind, with or without stock."""
    from src.domains.supplier.inventory.repositories.inventory_repository import (
        InventoryRepository,
    )
    from src.domains.supplier.products.models.supplier_offer import (
        ProductCategory,
        ProductUnit,
    )
    from src.domains.supplier.products.repositories.supplier_offer_repository import (
        SupplierOfferRepository,
    )

    def _make(name, *, kind=SupplierKind.WHOLESALER, verified=True, with_stock=True,
              tier=SupplierPlanTier.FREE):
        n = next(_seq)
        user = make_supplier(f"explore{n}@example.com")
        profile = make_supplier_profile(
            user,
            business_name=name,
            verification_status=(
                SupplierVerificationStatus.VERIFIED
                if verified
                else SupplierVerificationStatus.UNVERIFIED
            ),
        )
        profile.supplier_kind = kind
        profile.plan_tier = tier
        db.session.commit()

        if with_stock:
            product = SupplierOfferRepository.create(
                profile.id, f"Thing {n}", ProductCategory.OTHER, 1000, ProductUnit.EACH,
                sku=f"SKU-EXP-{n}", product_code=f"PC-EXP-{n}",
            )
            inventory = InventoryRepository.get_or_create_for_product(product.id, profile.id)
            InventoryRepository.adjust_quantity(inventory, 10)
            db.session.commit()
        return profile

    return _make


def _names(profiles):
    return [p.business_name for p in profiles]


class TestTheNameDecidesNothing:
    def test_a_wholesaler_without_the_word_is_listed(
        self, app, db_session, make_business, supplier_of
    ):
        """"Seshego Cash & Carry" says nothing in its name and is
        exactly what this screen is for."""
        business = make_business("explore-biz-a@example.com")
        supplier_of("Seshego Cash & Carry", kind=SupplierKind.WHOLESALER)

        assert "Seshego Cash & Carry" in _names(explore_service.wholesalers(business.id))

    def test_a_retailer_with_the_word_is_not(
        self, app, db_session, make_business, supplier_of
    ):
        """THE TRAP. They have done nothing wrong; they are simply not
        a wholesaler, and a keyword filter could not tell."""
        business = make_business("explore-biz-b@example.com")
        supplier_of("Wholesale Beauty Supplies", kind=SupplierKind.RETAILER)

        assert _names(explore_service.wholesalers(business.id)) == []

    def test_an_unspecified_supplier_is_not_guessed_into_a_kind(
        self, app, db_session, make_business, supplier_of
    ):
        business = make_business("explore-biz-c@example.com")
        supplier_of("Mbuyelo Wholesalers", kind=SupplierKind.UNSPECIFIED)

        assert _names(explore_service.wholesalers(business.id)) == []


class TestTheCurtainApplies:
    def test_an_unverified_wholesaler_does_not_appear(
        self, app, db_session, make_business, supplier_of
    ):
        """The most discovery-shaped surface in the app."""
        business = make_business("explore-biz-d@example.com")
        supplier_of("Pending Wholesale", verified=False)

        assert _names(explore_service.wholesalers(business.id)) == []


class TestAnEmptyCatalogueIsNotAResult:
    def test_a_wholesaler_with_no_stock_is_not_listed(
        self, app, db_session, make_business, supplier_of
    ):
        """ordering_gate already refuses an order from one; listing
        them is offering a door known to be locked."""
        business = make_business("explore-biz-e@example.com")
        supplier_of("Empty Wholesale", with_stock=False)

        assert _names(explore_service.wholesalers(business.id)) == []

    def test_a_supplier_is_listed_once_however_much_stock_they_have(
        self, app, db_session, make_business, supplier_of
    ):
        """The join to products must not multiply the supplier."""
        from src.domains.supplier.products.models.supplier_offer import (
            ProductCategory,
            ProductUnit,
        )
        from src.domains.supplier.products.repositories.supplier_offer_repository import (
            SupplierOfferRepository,
        )

        business = make_business("explore-biz-f@example.com")
        profile = supplier_of("Big Wholesale")
        for i in range(3):
            SupplierOfferRepository.create(
                profile.id, f"Extra {i}", ProductCategory.OTHER, 500, ProductUnit.EACH,
                sku=f"SKU-EXTRA-{next(_seq)}", product_code=f"PC-EX-{next(_seq)}",
            )
        db.session.commit()

        assert _names(explore_service.wholesalers(business.id)).count("Big Wholesale") == 1


class TestTierOrdersTheEqualsHere:
    def test_a_paying_wholesaler_comes_first(
        self, app, db_session, make_business, supplier_of
    ):
        """DEFENSIBLE ON THIS SCREEN because it shows no distance and no
        score, so its order is not a claim the reader can check -- and
        because somebody who opened "Explore wholesalers" came to look
        at suppliers."""
        business = make_business("explore-biz-g@example.com")
        supplier_of("Aardvark Wholesale", tier=SupplierPlanTier.FREE)
        supplier_of("Zebra Wholesale", tier=SupplierPlanTier.MAX)

        assert _names(explore_service.wholesalers(business.id))[0] == "Zebra Wholesale"

    def test_equal_plans_fall_back_to_the_alphabet(
        self, app, db_session, make_business, supplier_of
    ):
        business = make_business("explore-biz-h@example.com")
        supplier_of("Zebra Wholesale", tier=SupplierPlanTier.PRO)
        supplier_of("Aardvark Wholesale", tier=SupplierPlanTier.PRO)

        assert _names(explore_service.wholesalers(business.id)) == [
            "Aardvark Wholesale",
            "Zebra Wholesale",
        ]


class TestTheChipsAreBuiltFromWhatExists:
    def test_a_kind_with_nobody_is_not_offered(self, app, db_session, supplier_of):
        """An empty result from a chip the app drew itself reads as
        broken; a chip that is not there reads as "not yet"."""
        supplier_of("Only Wholesale", kind=SupplierKind.WHOLESALER)

        kinds = explore_service.kinds_with_suppliers()

        assert kinds == ["WHOLESALER"]

    def test_unspecified_is_never_a_chip(self, app, db_session, supplier_of):
        """"Browse the ones who did not tell us what they are" is not a
        thing anybody wants to tap."""
        supplier_of("Unsaid Co", kind=SupplierKind.UNSPECIFIED)

        assert "UNSPECIFIED" not in explore_service.kinds_with_suppliers()


class TestTheDoorIntoExploreSitsAtTheBottomOfTheFeed:
    """THE PLACEMENT IS THE DESIGN, so the placement is what is tested.

    Explore was reachable only from the overflow menu, whose own
    comment argues that browsing by what a supplier IS is "an
    occasional, deliberate act ... not something to put in front of
    somebody who opened this tab to check their connections". That
    reasoning survives ONLY while this section is last. Anywhere else
    in the feed and the comment and the code contradict each other --
    which is exactly the sort of drift a test about ordering is for.
    """

    def test_it_is_the_last_section_in_the_feed(
        self, app, db_session, make_business, supplier_of
    ):
        """Everything above it is a supplier the shop has some claim on
        -- history, a declaration, an invitation, proximity. This is
        the door to the ones it has none on, and reaching it should
        mean somebody went looking."""
        from src.domains.network.community.services import feed_service

        supplier_of("Lepelle Wholesalers", kind=SupplierKind.WHOLESALER)
        business = make_business()

        sections = feed_service.feed_for(business.id, "business")

        assert sections, "the feed should not be empty"
        assert sections[-1]["type"] == "EXPLORE_KINDS"

    def test_no_kinds_means_no_section_rather_than_an_empty_one(
        self, app, db_session, make_business, supplier_of
    ):
        """A platform whose visible suppliers have all left
        supplier_kind at UNSPECIFIED has nothing to offer here. A
        titled box with no doors in it is worse than no box."""
        from src.domains.network.community.services import feed_service

        supplier_of("Unsaid Co", kind=SupplierKind.UNSPECIFIED)
        business = make_business()

        sections = feed_service.feed_for(business.id, "business")

        assert all(s["type"] != "EXPLORE_KINDS" for s in sections)

    def test_it_offers_only_kinds_that_have_somebody(
        self, app, db_session, make_business, supplier_of
    ):
        """The feed must not advertise a door that opens onto an empty
        room. It asks the same function the Explore screen's own chip
        row asks, so the two can never disagree."""
        from src.domains.network.community.services import feed_service

        supplier_of("Lepelle Wholesalers", kind=SupplierKind.WHOLESALER)
        supplier_of("Empty Shelf Mfg", kind=SupplierKind.MANUFACTURER, with_stock=False)
        business = make_business()

        section = next(
            s
            for s in feed_service.feed_for(business.id, "business")
            if s["type"] == "EXPLORE_KINDS"
        )

        assert section["kinds"] == ["WHOLESALER"]

    def test_it_sends_raw_kinds_and_never_labels(
        self, app, db_session, make_business, supplier_of
    ):
        """DELIBERATELY UNLIKE CATEGORY_CHIPS, which ships a label and
        an icon because the app cannot invent an icon for a category it
        has not heard of. A kind needs neither: the app's
        SUPPLIER_KIND_LABELS already owns the rule that a chip is
        PLURAL, and labelForKind title-cases anything unrecognised.
        A second copy of that rule arriving from here is how the two
        drift apart -- so this asserts the shape, not just the values.
        """
        from src.domains.network.community.services import feed_service

        supplier_of("Lepelle Wholesalers", kind=SupplierKind.WHOLESALER)
        business = make_business()

        section = next(
            s
            for s in feed_service.feed_for(business.id, "business")
            if s["type"] == "EXPLORE_KINDS"
        )

        assert section["kinds"] == ["WHOLESALER"], "raw enum values, not 'Wholesalers'"
        assert all(isinstance(k, str) for k in section["kinds"])
