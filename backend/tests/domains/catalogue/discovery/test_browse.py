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
        """ASSERTS THE FACTS, NOT THE DICT. This compared the whole
        payload for equality and broke the moment the browse gained
        facets -- which is a test failing because the code improved.
        The rule being defended is that an empty category ANSWERS
        rather than raises, so that is what is checked."""
        result = browse_service.browse_category(category="HARDWARE_GENERAL")

        assert result["products"] == []
        assert result["hasMore"] is False

    def test_an_empty_category_still_reports_a_total_of_zero(self, app, db_session):
        """THE HEADER HAS TO SAY SOMETHING. "0 offers" is a fact a
        reader can act on; a missing count leaves the bar looking
        half-drawn, which reads as the screen having failed rather than
        the category being empty."""
        result = browse_service.browse_category(category="HARDWARE_GENERAL")

        assert result["total"] == 0
        assert result["kinds"] == []

    def test_facets_are_sent_once_per_filter_not_once_per_page(self, app, db_session):
        """THEY COST A QUERY EACH. The count and the brand rollup are
        fetched at offset zero and omitted afterwards, so a long scroll
        is one extra pair of queries rather than one pair per page --
        the same query-cost-per-open problem the feed carries."""
        first = browse_service.browse_category(category="FOOD_GROCERY", offset=0)
        later = browse_service.browse_category(category="FOOD_GROCERY", offset=24)

        assert "total" in first and "kinds" in first
        assert "total" not in later and "kinds" not in later


class TestNarrowingTheCategory:
    """THE CONTROLS THAT MAKE A CATEGORY USABLE.

    Seventeen flat categories mean "Food & Grocery" is one bucket
    holding flour, oil, sugar and rice. Nobody browses a thousand
    products -- a shopkeeper opens the screen wanting cooking oil -- so
    these are not decoration on a list, they are the reason the list can
    be used at all.

    WHAT THESE DEFEND, worst consequence first:

      SORTING IS THE QUERY'S JOB, NOT THE PAGE'S. "Cheapest first"
      applied to the twenty-four rows the database happened to return
      is false in the only way that matters, and it is false silently.

      AN EMPTY FILTER IS AN EMPTY RESULT, NOT AN IGNORED ONE. A shop
      with no connections asking for "my suppliers" has asked for the
      empty set; answering with the whole market is the screen
      overriding the control the reader just used.

      THE FACETS AGREE WITH THE LIST. A header counting one thing above
      a list built from another is worse than no header.
    """

    def test_cheapest_first_orders_the_whole_category_not_the_page(
        self, app, db_session, offer_from
    ):
        for price in (5000, 700, 2500, 100):
            offer_from(f"Oil {price}", price_cents=price, category=ProductCategory.FOOD_GROCERY)

        result = browse_service.browse_category(
            category="FOOD_GROCERY", sort="price_asc", limit=2
        )

        prices = [p["priceCents"] for p in result["products"]]
        assert prices == [100, 700], "the two cheapest in the CATEGORY, not on a page"

    def test_most_expensive_first_is_the_exact_reverse(self, app, db_session, offer_from):
        for price in (5000, 700, 2500):
            offer_from(f"Oil {price}", price_cents=price, category=ProductCategory.FOOD_GROCERY)

        result = browse_service.browse_category(
            category="FOOD_GROCERY", sort="price_desc", limit=1
        )

        assert result["products"][0]["priceCents"] == 5000

    def test_an_unknown_sort_is_a_boring_page_not_an_error(
        self, app, db_session, offer_from
    ):
        """A stale app sending a sort this server has never heard of
        must get the default, not a 500. The value chooses an ORDER BY,
        so it is validated against the list rather than passed through."""
        offer_from("Anything", category=ProductCategory.FOOD_GROCERY)

        result = browse_service.browse_category(category="FOOD_GROCERY", sort="popularity")

        assert len(result["products"]) == 1

    def test_my_suppliers_with_no_connections_is_empty_not_everything(
        self, app, db_session, offer_from, make_business
    ):
        """THE FILTER THAT COULD SILENTLY INVERT ITSELF. `None` means no
        filter and `[]` means nothing matches, and confusing the two
        shows a shop the entire market at the exact moment they asked
        to see only their own suppliers."""
        offer_from("Someone else's stock", category=ProductCategory.FOOD_GROCERY)
        business = make_business()

        result = browse_service.browse_category(
            business_id=business.id, category="FOOD_GROCERY", mine_only=True
        )

        assert result["products"] == []
        assert result["total"] == 0

    def test_without_the_filter_the_same_shop_sees_the_market(
        self, app, db_session, offer_from, make_business
    ):
        """Browsing is open at the platform level -- the connection
        gates ORDERING, never seeing. "My suppliers" is the shop
        choosing to see less, which is a different thing."""
        offer_from("Someone else's stock", category=ProductCategory.FOOD_GROCERY)
        business = make_business()

        result = browse_service.browse_category(
            business_id=business.id, category="FOOD_GROCERY"
        )

        assert len(result["products"]) == 1

    def test_search_narrows_the_count_as_well_as_the_list(
        self, app, db_session, offer_from
    ):
        """THE HEADER AND THE LIST COME FROM ONE FILTER BUILDER. A count
        that ignored the search would print "253 offers" above four
        results, every time anybody typed."""
        offer_from("Sunfoil Cooking Oil 2L", category=ProductCategory.FOOD_GROCERY)
        offer_from("White Sugar 2.5kg", category=ProductCategory.FOOD_GROCERY)

        result = browse_service.browse_category(category="FOOD_GROCERY", search="oil")

        assert result["total"] == 1
        assert len(result["products"]) == 1


class TestEveryNumberOnScreenIsTheNumberYouGet:
    """THE BUG A REAL SCREENSHOT CAUGHT.

    A brand chip read "Iwisa 16" and opened onto THREE cards. Both
    numbers were true: sixteen Iwisa offers from six wholesalers are
    three catalogue products -- Maize Meal in 2.5kg, 5kg and 25kg. The
    count said offers, the grid drew cards, and the label "offers" was
    a disclaimer rather than a fix.

    IT IS THE WORST CLASS OF WRONG NUMBER, because nothing crashes and
    nothing logs. A reader simply learns that the numbers on this screen
    cannot be trusted, and after that no amount of correctness anywhere
    else on it earns the trust back.

    THE RULE: any number this screen prints is a PROMISE about what
    happens when you act on it. _card_key is _group_by_product's key
    written in SQL so the two can never drift.
    """

    def test_the_header_count_is_what_the_grid_renders(
        self, app, db_session, offer_from
    ):
        """Three suppliers, one product, ONE card -- and the header has
        to say one."""
        from src.domains.catalogue.products.models.product import Product
        from src.domains.catalogue.products.models.taxonomy import ProductCategory as PC

        product = Product(
            name="Iwisa Maize Meal 5kg",
            normalized_name="iwisa maize meal 5kg",
            category=PC.FOOD_GROCERY,
        )
        db_session.add(product)
        db_session.commit()

        for price in (6550, 6700, 6400):
            offer_from(
                "Iwisa Maize Meal 5kg",
                price_cents=price,
                category=ProductCategory.FOOD_GROCERY,
                product_id=product.id,
            )

        result = browse_service.browse_category(category="FOOD_GROCERY", limit=100)

        assert result["total"] == 1, "three offers of one product are ONE card"
        assert len(result["products"]) == result["total"]

    def test_an_unmatched_offer_counts_as_its_own_card(
        self, app, db_session, offer_from
    ):
        """The other half of the grouping rule. An offer with no
        catalogue product stands alone -- we do not know it is the same
        thing as anything else, and that judgement belongs to the
        matching ladder, not to a COUNT."""
        offer_from("Something nobody matched", category=ProductCategory.FOOD_GROCERY)
        offer_from("Something else nobody matched", category=ProductCategory.FOOD_GROCERY)

        result = browse_service.browse_category(category="FOOD_GROCERY", limit=100)

        assert result["total"] == 2
        assert len(result["products"]) == 2

    def test_a_kind_chip_promises_what_it_opens(
        self, app, db_session, offer_from, make_supplier, make_supplier_profile
    ):
        """WHAT THE SCREENSHOT SHOWED, now against the chips that
        replaced the brands. The chip's number and the result of tapping
        it are the same number, or the chip is a lie.

        BRAND CHIPS WERE THE FIRST ANSWER AND ARE GONE: a category has
        dozens of brands and four supplier kinds, and typing "Huletts"
        answers the brand question better than a finite row ever could.
        The count bug they exposed is what this test keeps.
        """
        from src.domains.catalogue.products.models.product import Product
        from src.domains.catalogue.products.models.taxonomy import ProductCategory as PC
        from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierKind

        user = make_supplier("kindchip@example.com")
        profile = make_supplier_profile(
            user, business_name="Kind Wholesaler", supplier_kind=SupplierKind.WHOLESALER
        )

        for size in ("2.5kg", "5kg", "25kg"):
            product = Product(
                name=f"Iwisa Maize Meal {size}",
                normalized_name=f"iwisa maize meal {size}",
                category=PC.FOOD_GROCERY,
            )
            db_session.add(product)
            db_session.commit()
            # Several offers of each size from the SAME wholesaler --
            # the exact shape that made an offer count diverge from a
            # card count.
            for price in (3750, 3900, 4100):
                offer_from(
                    f"Iwisa Maize Meal {size}",
                    price_cents=price,
                    category=ProductCategory.FOOD_GROCERY,
                    product_id=product.id,
                    profile=profile,
                )

        listing = browse_service.browse_category(category="FOOD_GROCERY", limit=100)
        chip = next(k for k in listing["kinds"] if k["id"] == "WHOLESALER")

        opened = browse_service.browse_category(
            category="FOOD_GROCERY", kind="WHOLESALER", limit=100
        )

        assert chip["count"] == 3, "nine offers, three products"
        assert len(opened["products"]) == chip["count"]

    def test_paging_never_repeats_or_skips_a_product(
        self, app, db_session, offer_from
    ):
        """THE BUG REACT REPORTED AS A DUPLICATE KEY, which was really a
        paging bug. offset was applied to OFFER ROWS while the caller
        advanced it by CARDS RECEIVED, so page two re-read rows page one
        had already grouped -- and further down, the same arithmetic
        skipped products with nothing to report it.

        Walking every page and comparing against the header is the only
        assertion that catches both halves at once.
        """
        for index in range(30):
            offer_from(f"Product {index:02d}", category=ProductCategory.FOOD_GROCERY)

        seen, offset = [], 0
        while True:
            page = browse_service.browse_category(
                category="FOOD_GROCERY", limit=7, offset=offset
            )
            ids = [p["id"] for p in page["products"]]
            if not ids:
                break
            seen += ids
            offset += len(ids)
            if not page["hasMore"]:
                break

        total = browse_service.browse_category(category="FOOD_GROCERY")["total"]

        assert len(seen) == len(set(seen)), "a product appeared on two pages"
        assert len(seen) == total, "the walk did not reach every product"


class TestTheChipsSurviveBeingUsed:
    """THE TRAP A FILTER ROW SETS FOR ITSELF.

    Facets counted AFTER their own filter is applied leave exactly one
    chip standing -- the one just tapped. The row collapses, the other
    options vanish, and the only way back is a filter the reader can no
    longer see. It reads as the screen breaking at the moment it was
    used correctly.

    THE RULE: a chip row shows the ALTERNATIVES to the current choice,
    so the current choice must not narrow it. Search is different and is
    applied first -- it changes what the question is ABOUT, so the chips
    should answer it.
    """

    def test_choosing_a_supplier_keeps_the_other_supplier_chips(
        self, app, db_session, offer_from
    ):
        # offer_from creates a FRESH supplier per call unless told
        # otherwise, so three calls are three wholesalers -- which is
        # what makes "the others are still there" a real assertion.
        for size in ("1kg", "2kg", "5kg"):
            offer_from(f"Sugar {size}", category=ProductCategory.FOOD_GROCERY)

        listing = browse_service.browse_category(category="FOOD_GROCERY", limit=99)
        assert len(listing["suppliers"]) >= 2, "need alternatives for this to mean anything"

        chosen = listing["suppliers"][0]
        after = browse_service.browse_category(
            category="FOOD_GROCERY", supplier=chosen["id"], limit=99
        )

        assert len(after["suppliers"]) == len(listing["suppliers"]), (
            "the other suppliers vanished -- the facets were counted after "
            "their own filter"
        )
        assert after["total"] == chosen["count"], "but the PRODUCTS did narrow"

    def test_choosing_a_kind_keeps_the_other_kind_chips(
        self, app, db_session, offer_from, make_supplier, make_supplier_profile
    ):
        from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierKind

        for label, kind in (("W Co", SupplierKind.WHOLESALER), ("M Co", SupplierKind.MANUFACTURER)):
            user = make_supplier(f"{label.replace(' ', '').lower()}@example.com")
            profile = make_supplier_profile(user, business_name=label, supplier_kind=kind)
            offer_from(f"{label} stock", category=ProductCategory.FOOD_GROCERY, profile=profile)

        listing = browse_service.browse_category(category="FOOD_GROCERY", limit=99)
        assert len(listing["kinds"]) == 2

        after = browse_service.browse_category(
            category="FOOD_GROCERY", kind="WHOLESALER", limit=99
        )

        assert len(after["kinds"]) == 2, "the other kind vanished"
        assert after["total"] == 1
