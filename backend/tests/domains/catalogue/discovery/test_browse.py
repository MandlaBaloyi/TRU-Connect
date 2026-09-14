"""
Browsing the catalogue across every supplier.

THE QUERY THAT MAKES A CATEGORY CHIP MEAN SOMETHING. Before this,
tapping "Drinks" routed to SUPPLIER search and found shops rather than
drinks -- the first thing a new user does was the thing that worked
least.

WHAT THESE DEFEND, worst consequence first:

  THE CURTAIN. An unverified supplier's stock must not be browsable.
  Discovery is exactly where a bypass hides, because nobody notices an
  EXTRA product. This is the only failure here with a victim.

  IT MUST WORK WITH AN EMPTY CATALOGUE. On the day this was written
  there were 28 supplier offers, ZERO matched and ZERO catalogue
  products. A catalogue-first browse would have returned an empty
  screen and looked like a bug. Grouping by product is what makes the
  result BETTER when matching has run; it is not what makes it
  possible.

  ONE CARD PER PRODUCT, NOT PER SUPPLIER. When three wholesalers carry
  the same sugar, a shopper should choose a supplier -- not squint at
  three spellings of the same bag.

  AN UNBUYABLE CARD IS WORSE THAN NO CARD, except when silence is
  worse: out of stock is information a shop can act on, a supplier they
  cannot pay is a dead end at the last step of checkout. The two are
  handled differently on purpose.
"""
from __future__ import annotations

from itertools import count

import pytest

from src.domains.catalogue.discovery.repositories import catalogue_browse_repository
from src.domains.catalogue.discovery.services import browse_service, offer_selection
from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
from src.extensions import db

_seq = count()


@pytest.fixture()
def offer_from(make_supplier, make_supplier_profile):
    """An offer from a fresh visible supplier, unless told otherwise."""
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer

    def _make(
        name,
        *,
        price_cents=1500,
        category=ProductCategory.BEVERAGES,
        product_id=None,
        profile=None,
        archived=False,
    ):
        n = next(_seq)
        if profile is None:
            user = make_supplier(f"browse{n}@example.com")
            profile = make_supplier_profile(user, business_name=f"Wholesaler {n}")
        offer = SupplierOffer(
            supplier_profile_id=profile.id,
            name=name,
            category=category,
            price_cents=price_cents,
            selling_unit=ProductUnit.EACH,
            sku=f"SKU-BR-{n}",
            product_code=f"PC-BR-{n}",
            product_id=product_id,
            is_archived=archived,
        )
        db.session.add(offer)
        db.session.commit()
        return offer, profile

    return _make


class TestTheCurtain:
    def test_an_unverified_supplier_is_not_browsable(
        self, app, db_session, offer_from, make_supplier, make_supplier_profile
    ):
        """THE ONE FAILURE HERE WITH A VICTIM -- a business ordering
        from somebody the platform has not checked. Nobody notices an
        extra card, which is why this is a test."""
        from src.domains.supplier.supplier_profile.models.supplier_profile import (
            SupplierVerificationStatus,
        )

        offer_from("Visible Cola 2L")
        user = make_supplier("hidden-browse@example.com")
        hidden = make_supplier_profile(user, business_name="Not Checked")
        hidden.verification_status = SupplierVerificationStatus.UNVERIFIED
        db.session.commit()
        offer_from("Hidden Cola 2L", profile=hidden)

        groups = catalogue_browse_repository.browse(category="BEVERAGES")

        names = [o.name for group in groups for o in group]
        assert "Visible Cola 2L" in names
        assert "Hidden Cola 2L" not in names


class TestItWorksBeforeMatchingDoes:
    def test_unmatched_offers_each_stand_alone(self, app, db_session, offer_from):
        """ZERO catalogue products existed when this was written. If
        browse required a matched product it would return nothing, and
        a chip leading to an empty screen looks like a broken app."""
        offer_from("Cola 2L")
        offer_from("Fanta 2L")
        offer_from("Sprite 2L")

        groups = catalogue_browse_repository.browse(category="BEVERAGES")

        assert len(groups) == 3
        assert all(len(g) == 1 for g in groups)

    def test_matched_offers_collapse_into_one_card(self, app, db_session, offer_from):
        """THE CATALOGUE MADE VISIBLE. Three spellings of the same bag
        become one card and a choice of supplier -- and this is the
        thing a competitor without a resolved catalogue cannot draw."""
        from src.domains.catalogue.products.models.product import Product

        product = Product(
            name="White Sugar 2.5kg",
            normalized_name="white sugar 2.5kg",
            category=ProductCategory.FOOD_GROCERY,
        )
        db.session.add(product)
        db.session.flush()

        for spelling, price in [("WHT SUGR 2.5KG", 4500), ("White Sugar 2.5kg", 4200), ("Sugar White 2.5KG", 4800)]:
            offer_from(spelling, price_cents=price, category=ProductCategory.FOOD_GROCERY, product_id=product.id)

        groups = catalogue_browse_repository.browse(category="FOOD_GROCERY")

        assert len(groups) == 1, "three offers of one product should be ONE card"
        assert len(groups[0]) == 3
        assert offer_selection.alternatives_count(groups[0], groups[0][0]) == 2

    def test_two_suppliers_spelling_it_alike_are_not_assumed_to_match(
        self, app, db_session, offer_from
    ):
        """NEVER GROUPED BY NAME. Deciding two strings are the same
        product is the matching ladder's judgement, made with a
        confidence score and a review queue. Doing it here with a string
        comparison would be that whole system done badly in one line."""
        offer_from("Coca-Cola 2L")
        offer_from("Coca-Cola 2L")

        groups = catalogue_browse_repository.browse(category="BEVERAGES")

        assert len(groups) == 2


class TestWhatIsExcluded:
    def test_archived_offers_are_not_browsable(self, app, db_session, offer_from):
        offer_from("Live Cola")
        offer_from("Old Cola", archived=True)

        names = [o.name for g in catalogue_browse_repository.browse(category="BEVERAGES") for o in g]

        assert names == ["Live Cola"]

    def test_a_category_filter_actually_filters(self, app, db_session, offer_from):
        offer_from("Cola 2L", category=ProductCategory.BEVERAGES)
        offer_from("Brown Bread", category=ProductCategory.BAKERY)

        names = [o.name for g in catalogue_browse_repository.browse(category="BAKERY") for o in g]

        assert names == ["Brown Bread"]

    def test_search_escapes_wildcards(self, app, db_session, offer_from):
        """A shopper typing "50%" is searching for "50%", not asking to
        match everything. test_like_escaping.py exists because this was
        got wrong once already elsewhere."""
        offer_from("50% Off Cola")
        offer_from("Plain Cola")

        names = [o.name for g in catalogue_browse_repository.browse(search="50%") for o in g]

        assert names == ["50% Off Cola"]


class TestWhichOfferIsShown:
    def _offer(self, oid, price, supplier):
        return type("O", (), {"id": oid, "price_cents": price, "supplier_profile_id": supplier})()

    def test_cheapest_wins_among_strangers(self):
        group = [self._offer("a", 1500, "s1"), self._offer("b", 1200, "s2")]

        assert offer_selection.select(group).id == "b"

    def test_their_own_supplier_beats_a_cheaper_stranger(self):
        """SWITCHING SUPPLIERS IS A RELATIONSHIP DECISION and the feed
        must not make it quietly on somebody's behalf."""
        group = [self._offer("a", 1800, "mine"), self._offer("b", 1200, "stranger")]

        assert offer_selection.select(group, incumbent_supplier_ids={"mine"}).id == "a"

    def test_a_supplier_they_cannot_pay_is_dropped_entirely(self):
        """Not a weaker option -- a dead end at the last step of
        checkout, which is the worst possible moment to find out."""
        group = [self._offer("a", 1200, "unpayable")]

        assert offer_selection.select(group, payable_supplier_ids=set()) is None

    def test_out_of_stock_still_shows_rather_than_vanishing(self):
        """OUT OF STOCK IS INFORMATION -- ask, wait, look elsewhere.
        Silence is not. Deliberately different from the payment case."""
        group = [self._offer("a", 1200, "s1")]

        assert offer_selection.select(group, in_stock_ids=set()) is not None

    def test_the_same_group_resolves_the_same_way_every_time(self):
        """A card that changes supplier under a thumb is one nobody can
        trust."""
        group = [self._offer("b", 1200, "s1"), self._offer("a", 1200, "s2")]

        first = offer_selection.select(group).id
        second = offer_selection.select(list(reversed(group))).id

        assert first == second


class TestTheServiceLayer:
    def test_a_card_names_its_supplier(self, app, db_session, offer_from):
        """A browse mixes suppliers where a shopfront never does, so a
        card that does not say whose it is sends a shopkeeper to the
        wrong shop."""
        offer_from("Cola 2L")

        result = browse_service.browse_category(category="BEVERAGES")

        assert len(result["products"]) == 1
        card = result["products"][0]
        assert card["supplierName"]
        assert card["supplierId"]
        assert card["alternativeCount"] == 0

    def test_an_empty_category_is_empty_not_an_error(self, app, db_session):
        result = browse_service.browse_category(category="HARDWARE_GENERAL")

        assert result == {"products": [], "hasMore": False}
