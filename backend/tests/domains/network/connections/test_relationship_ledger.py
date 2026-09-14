"""
My Connections is a RELATIONSHIP LEDGER, not a contact list (V2_04 2.3).

    Per row:  avatar and name, last ordered, typical reorder gap when
              there is enough history, an outstanding order if one is open
    Ordered:  open order first, then reorder-due, then recency

WHAT THESE TESTS ACTUALLY DEFEND, worst consequence first:

  A NEVER-TRADED CONNECTION MUST NOT LOOK OVERDUE. Right after
  connecting, two parties have no history at all. Rendering that as
  "overdue" would send a shopkeeper to chase an order they never placed,
  and it is the single easiest mistake to make here because "no last
  order" and "a very old last order" both mean "nothing recent".

  ONE ORDER IS NOT A PATTERN, for the same reason it is not one in the
  supplier feed: a rhythm invented from a single point is a guess
  wearing the clothes of a fact.

  THE ORDER OF THE LIST IS THE FEATURE. A ledger sorted alphabetically
  is a contact list. The whole claim of V2_04 2.3 is that the row you
  need is at the top, and that claim is one careless `sorted()` away
  from being false.

The ordering is tested on PLAIN DICTS rather than through the database,
because the rule is a pure function and deserves to be pinned as one --
a database round trip would make these slow without testing anything
more. The integration test at the bottom is what proves the fields
actually reach the endpoint's payload.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from src.core.base_model import utcnow
from src.domains.network.connections.services.connection_list_service import (
    _as_ledger,
    _trading_facts,
)


def _row(name, *, open_order=False, overdue=False, last_days_ago=None):
    now = utcnow()
    return {
        "name": name,
        "openOrder": {"id": "x", "status": "PENDING_SUPPLIER_APPROVAL"} if open_order else None,
        "isOverdue": overdue,
        "lastOrderAt": (
            (now - timedelta(days=last_days_ago)).isoformat() if last_days_ago is not None else None
        ),
    }


class TestTheOrderIsTheFeature:
    def test_open_order_outranks_everything(self):
        rows = _as_ledger(
            [
                _row("recent", last_days_ago=1),
                _row("overdue", overdue=True, last_days_ago=60),
                _row("has an open order", open_order=True, last_days_ago=200),
            ]
        )

        # Oldest last order of the three, and still first: somebody is
        # waiting on somebody.
        assert rows[0]["name"] == "has an open order"

    def test_overdue_outranks_recent(self):
        rows = _as_ledger(
            [
                _row("ordered yesterday", last_days_ago=1),
                _row("usually orders weekly, silent a month", overdue=True, last_days_ago=30),
            ]
        )

        assert [r["name"] for r in rows] == [
            "usually orders weekly, silent a month",
            "ordered yesterday",
        ]

    def test_then_most_recent_first(self):
        rows = _as_ledger(
            [
                _row("three weeks", last_days_ago=21),
                _row("yesterday", last_days_ago=1),
                _row("a week", last_days_ago=7),
            ]
        )

        assert [r["name"] for r in rows] == ["yesterday", "a week", "three weeks"]

    def test_never_traded_sinks_but_survives(self):
        """A supplier you connected to and have not ordered from is a
        REAL relationship -- it belongs at the bottom, not missing."""
        rows = _as_ledger([_row("never ordered"), _row("ordered once", last_days_ago=40)])

        assert [r["name"] for r in rows] == ["ordered once", "never ordered"]
        assert len(rows) == 2


class TestWhatTheRowSays:
    def test_a_fresh_connection_is_blank_not_overdue(self):
        """THE MISTAKE THIS STOPS: treating "no last order" the same as
        "a very old last order". Both mean nothing recent; only one of
        them means somebody is late."""
        facts = _trading_facts(None, None, utcnow())

        assert facts["orderCount"] == 0
        assert facts["lastOrderAt"] is None
        assert facts["typicalGapDays"] is None
        assert facts["isOverdue"] is False
        assert facts["openOrder"] is None

    def test_one_order_is_not_a_pattern(self):
        now = utcnow()

        facts = _trading_facts([now - timedelta(days=90)], None, now)

        assert facts["orderCount"] == 1
        assert facts["typicalGapDays"] is None
        assert facts["isOverdue"] is False

    def test_a_rhythm_produces_a_gap(self):
        now = utcnow()

        facts = _trading_facts([now - timedelta(days=d) for d in (28, 21, 14, 7)], None, now)

        assert facts["typicalGapDays"] == pytest.approx(7.0, abs=0.5)
        assert facts["lastOrderAt"] is not None


class TestOpenMeansSomebodyIsWaiting:
    def test_confirmed_is_not_open(self):
        """There is no delivered or completed status in this model, so
        CONFIRMED is where a successful order ENDS. Counting it as open
        would leave every connection permanently showing an outstanding
        order, which makes the badge meaningless."""
        from src.domains.network.orders.models.stock_order import StockOrderStatus
        from src.domains.network.orders.repositories.stock_order_repository import (
            StockOrderRepository,
        )

        assert StockOrderStatus.CONFIRMED not in StockOrderRepository.OPEN_STATUSES
        assert StockOrderStatus.PENDING_SUPPLIER_APPROVAL in StockOrderRepository.OPEN_STATUSES

    def test_a_cart_is_never_an_order(self):
        """Counting carts would let an abandoned basket masquerade as a
        buying rhythm."""
        from src.domains.network.orders.models.stock_order import StockOrderStatus
        from src.domains.network.orders.repositories.stock_order_repository import (
            StockOrderRepository,
        )

        assert StockOrderStatus.CART in StockOrderRepository.RHYTHM_EXCLUDED_STATUSES
        assert StockOrderStatus.CART not in StockOrderRepository.OPEN_STATUSES


class TestItReachesThePayload:
    def test_a_business_sees_ledger_fields_on_every_row(
        self, app, db_session, make_business, make_supplier, make_supplier_profile
    ):
        """The pure tests above pin the RULE; this pins that the rule's
        output actually arrives in the response the app renders."""
        from src.domains.network.connections.repositories.connection_request_repository import (
            ConnectionRequestRepository,
        )
        from src.domains.network.connections.services import connection_list_service, request_service

        business = make_business("ledgerbuyer@example.com")
        supplier_user = make_supplier("ledgerseller@example.com")
        profile = make_supplier_profile(supplier_user, business_name="Ledger Wholesale")

        request_service.request_connection(business.id, profile.id)
        request = ConnectionRequestRepository.get_for_business_and_supplier(business.id, profile.id)
        request_service.approve_request(profile.supplier_id, request.id)

        rows = connection_list_service.get_my_connections(business.id, "business")

        assert len(rows) == 1
        row = rows[0]
        assert row["name"] == "Ledger Wholesale"
        # Connected, never traded -- present and honest, not absent.
        for key in ("orderCount", "lastOrderAt", "typicalGapDays", "isOverdue", "openOrder"):
            assert key in row, f"{key} missing from the connection row"
        assert row["orderCount"] == 0
        assert row["isOverdue"] is False
