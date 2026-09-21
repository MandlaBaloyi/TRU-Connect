"""
What the feed showed, and what was tapped.

WHAT THESE DEFEND, worst consequence first:

  THE GRAIN HOLDS. One row per (business, day, rail, position, item),
  however many times the tab is opened. If the upsert ever becomes an
  insert this table silently turns into the append-only event log the
  whole design exists to avoid -- and nothing fails until it is
  enormous, in production, months later. This is the test that fails
  first instead.

  POSITION IS RECORDED. tier_rules' own stated falsifier is "a tap-rate
  gap between the first and second card of a banded pair". A writer
  that loses position makes that sentence permanently unanswerable, and
  the 2km band can then never be argued with.

  THE DEMAND ENGINE CANNOT SEE A SUPPLIER THROUGH THIS. The table
  carries supplier_profile_id for billing; the engine is supplier-blind
  by architecture test, and that test parses imports rather than
  columns. The narrow read is what makes both true at once, so its
  shape is asserted rather than assumed.

  THE COUNTERS MEAN WHAT THEY SAY. delivered is written server-side at
  compose time; tapped comes from the device. A client that could
  assert `delivered` could manufacture the denominator of every tap
  rate in the system.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.domains.network.impressions.models.feed_impression import (
    FeedImpression,
    ImpressionItemType,
)
from src.domains.network.impressions.repositories.impression_repository import (
    ImpressionRepository,
    ImpressionRow,
)
from src.domains.network.impressions.services import impression_service


def _row(rail="buy-it-again", position=0, item_id="item-1", **kw):
    return ImpressionRow(
        rail=rail,
        position=position,
        item_id=item_id,
        item_type=kw.pop("item_type", ImpressionItemType.PRODUCT),
        **kw,
    )


def _stored(business_id):
    return list(ImpressionRepository.for_business(business_id))


class TestTheGrainHolds:
    def test_the_same_card_twice_in_one_day_is_one_row_with_two(
        self, app, db_session, make_business
    ):
        """THE TEST THIS TABLE EXISTS FOR. Ten thousand shops opening
        the tab three times a day is three million rows if this is ever
        an insert, and nothing else in the system would notice until it
        was far too late."""
        business = make_business()

        ImpressionRepository.bump(business.id, [_row()], column="delivered")
        ImpressionRepository.bump(business.id, [_row()], column="delivered")

        rows = _stored(business.id)
        assert len(rows) == 1
        assert rows[0].delivered == 2

    def test_a_different_position_is_a_different_row(
        self, app, db_session, make_business
    ):
        """POSITION IS PART OF THE KEY, not decoration on it. The same
        product at position 0 and position 4 are two different things
        that happened, and collapsing them is what makes tier_rules'
        falsifier unanswerable."""
        business = make_business()

        ImpressionRepository.bump(
            business.id,
            [_row(position=0), _row(position=4)],
            column="delivered",
        )

        assert sorted(r.position for r in _stored(business.id)) == [0, 4]

    def test_a_different_day_is_a_different_row(self, app, db_session, make_business):
        """Otherwise a counter incremented forever would say nothing
        about when, and every question in V2_19 is phrased per day."""
        business = make_business()
        yesterday = date.today() - timedelta(days=1)

        ImpressionRepository.bump(business.id, [_row()], column="delivered")
        ImpressionRepository.bump(business.id, [_row()], column="delivered", on=yesterday)

        assert len(_stored(business.id)) == 2

    def test_two_shops_never_share_a_row(self, app, db_session, make_business):
        """The business is part of the key. This is also the IDOR
        answer at the storage layer: there is no arrangement of inputs
        that makes one shop's tap land on another's counter."""
        # TWO DISTINCT EMAILS. make_business defaults to one address,
        # so calling it twice without naming them is a unique-violation
        # on auth.users rather than a second shop.
        one = make_business("shop-one@example.com")
        two = make_business("shop-two@example.com")

        ImpressionRepository.bump(one.id, [_row()], column="delivered")
        ImpressionRepository.bump(two.id, [_row()], column="delivered")

        assert len(_stored(one.id)) == 1
        assert len(_stored(two.id)) == 1

    def test_delivered_and_tapped_are_separate_counters_on_one_row(
        self, app, db_session, make_business
    ):
        """A tap does not create a second row, and it does not touch
        the denominator. Tap rate is only meaningful while those two
        facts hold together."""
        business = make_business()

        ImpressionRepository.bump(business.id, [_row()], column="delivered")
        ImpressionRepository.bump(business.id, [_row()], column="tapped")

        rows = _stored(business.id)
        assert len(rows) == 1
        assert (rows[0].delivered, rows[0].tapped) == (1, 1)

    def test_an_unknown_counter_is_refused(self, app, db_session, make_business):
        """The column name reaches the UPDATE clause, so a typo must
        fail here rather than as SQL."""
        business = make_business()

        with pytest.raises(ValueError):
            ImpressionRepository.bump(business.id, [_row()], column="seen")


class TestWalkingAComposedFeed:
    """The writer reads the PAYLOAD, not the section type, so a new
    section measures itself the day it ships."""

    def test_it_finds_products_suppliers_and_categories(self, app):
        sections = [
            {"id": "categories", "type": "CATEGORY_CHIPS",
             "categories": [{"value": "BAKERY"}, {"value": "DRINKS"}]},
            {"id": "buy-it-again", "type": "PRODUCT_RAIL",
             "products": [{"id": "p1", "supplierId": "s1"}]},
            {"id": "your-suppliers", "type": "SUPPLIER_RAIL",
             "suppliers": [{"id": "s9"}]},
        ]

        rows = impression_service.rows_for_sections(sections)

        assert len(rows) == 4
        assert {r.item_type for r in rows} == {
            ImpressionItemType.CATEGORY,
            ImpressionItemType.PRODUCT,
            ImpressionItemType.SUPPLIER,
        }

    def test_position_is_the_index_within_its_own_rail(self, app):
        """Not a running index across the whole feed -- the question is
        "position 2 of THIS rail", and a global counter would make
        every rail after the first unanswerable."""
        sections = [
            {"id": "rail-a", "products": [{"id": "a1"}, {"id": "a2"}]},
            {"id": "rail-b", "products": [{"id": "b1"}]},
        ]

        rows = impression_service.rows_for_sections(sections)

        by_rail = {(r.rail, r.position) for r in rows}
        assert by_rail == {("rail-a", 0), ("rail-a", 1), ("rail-b", 0)}

    def test_the_sponsored_card_is_counted(self, app):
        """THE ONE SECTION THAT PAYS, and the one shaped differently --
        a single "supplier" rather than a list. A loop that only
        understands plurals would leave the billable section as the one
        section with no data."""
        sections = [
            {"id": "sponsored", "type": "SPONSORED_SUPPLIER",
             "label": "Sponsored", "supplier": {"id": "s-paid"}}
        ]

        rows = impression_service.rows_for_sections(sections)

        assert len(rows) == 1
        assert rows[0].item_id == "s-paid"
        assert rows[0].supplier_profile_id == "s-paid"

    def test_a_product_card_carries_its_supplier_for_billing(self, app):
        sections = [{"id": "buy-it-again", "products": [{"id": "p1", "supplierId": "s1"}]}]

        (row,) = impression_service.rows_for_sections(sections)

        assert row.supplier_profile_id == "s1"

    def test_a_category_chip_carries_no_supplier(self, app):
        """Nullable on the model for exactly this row."""
        sections = [{"id": "categories", "categories": [{"value": "BAKERY"}]}]

        (row,) = impression_service.rows_for_sections(sections)

        assert row.supplier_profile_id is None
        assert row.item_id == "BAKERY"

    def test_sections_with_no_cards_are_skipped(self, app):
        """PROMO carries a banner and EXPLORE_KINDS carries doorways.
        Neither is an item a shop can want, and every falsifier this
        table answers is phrased about rails of products and suppliers.
        Deliberate, and one line to change when somebody asks."""
        sections = [
            {"id": "explore-kinds", "type": "EXPLORE_KINDS", "kinds": ["WHOLESALER"]},
            {"id": "promo", "type": "PROMO", "promo": {"title": "x"}},
        ]

        assert impression_service.rows_for_sections(sections) == []

    def test_a_card_with_no_identifier_is_skipped_not_guessed(self, app):
        """A row keyed on something invented is worse than no row --
        it would collide with a real one at the same position."""
        sections = [{"id": "rail", "products": [{"name": "no id here"}]}]

        assert impression_service.rows_for_sections(sections) == []


class TestTheDemandEngineGetsANarrowView:
    def test_the_considered_read_returns_categories_and_counts_only(
        self, app, db_session, make_business
    ):
        """THE SHAPE IS THE ENFORCEMENT. Dict[str, int] has no field a
        supplier could hide in, so leaking one would require changing
        this signature -- a visible act rather than an accident on a
        busy week. The architecture test parses imports, not columns;
        this is the half it cannot check."""
        business = make_business()

        result = ImpressionRepository.categories_considered(
            business.id, since=date.today() - timedelta(days=30)
        )

        assert isinstance(result, dict)
        assert all(isinstance(k, str) and isinstance(v, int) for k, v in result.items())

    def test_considered_signals_carry_no_supplier_field(self, app):
        """The dataclass the rest of the engine sees. Asserted here as
        well as in the repository because the two files will be read
        separately, and the guarantee needs to survive either one being
        edited alone."""
        from src.domains.business.demand.signals.considered import ConsideredSignals

        assert set(ConsideredSignals.__dataclass_fields__) == {"category_delivered"}

    def test_a_shop_with_no_impressions_is_empty_not_absent(
        self, app, db_session, make_business
    ):
        """Day one of every account. An empty signal is a correct
        answer; a crash is not."""
        from src.domains.business.demand.signals import considered

        signals = considered.considered_for(make_business().id)

        assert signals.is_empty
        assert signals.category_delivered == {}
