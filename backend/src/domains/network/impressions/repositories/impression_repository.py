"""
Reading and writing feed impressions.

THIS FILE IS THE BOUNDARY, not just the data access. The table has a
supplier_profile_id on it -- sponsored billing requires one -- and the
demand engine is SUPPLIER-BLIND by architecture test. Both facts are
true at once only because every read is defined here, and the one the
demand engine uses returns a shape that CANNOT carry a supplier.

See the note on categories_considered() below. That is the whole design
and it is why V2_19 refused to put this table under demand/: a record of
what the FEED did is not part of the demand model, and the engine gets a
narrow view of it rather than the table.

WHY network/impressions/ AND NOT network/community/impressions/, which
is what V2_19 proposed. Two rules are already enforced against the
community package and V2_19 was written without checking either:

    test_community_is_a_composer.py
      RULE 1  no domain may import the feed -- it is a composer, and
              the coordinator is never imported by what it coordinates
      RULE 2  the feed owns no tables -- "a composer that persists has
              stopped composing and started being a domain"

Rule 2 says exactly what this package is. An impressions table has rows,
so by this codebase's own definition it is a domain rather than part of
the composer, and it belongs beside community rather than inside it.

That also settles Rule 1 without an exception: the feed imports THIS
(a composer reading from a domain, which is the allowed direction), and
demand/ imports this rather than the feed. Both tests pass untouched.

V2_04 named impression logging as the one future exception to Rule 2 and
said it should "get its own reasoning, not this test quietly deleted".
This is the reasoning, and it turned out not to need the exception.

UPSERT, NOT INSERT. The grain -- one row per (business, day, rail,
position, item) -- is only bounded if the writer finds the existing row.
Postgres' ON CONFLICT DO UPDATE does that in one statement, which also
makes it correct under the concurrent writes the queue produces: two
threads composing feeds for the same shop cannot both insert.
"""
from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, Optional, Sequence
from uuid import UUID as UUIDType

from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.domains.network.impressions.models.feed_impression import (
    FeedImpression,
    ImpressionItemType,
)
from src.extensions import db


class ImpressionRow:
    """One card the composer returned, ready to be counted.

    A PLAIN CARRIER RATHER THAN THE MODEL, so the service can build a
    hundred of these without touching the session, and so the upsert
    below has one shape to read from whichever direction it was called.
    """

    __slots__ = ("rail", "position", "item_id", "item_type", "supplier_profile_id")

    def __init__(
        self,
        *,
        rail: str,
        position: int,
        item_id: str,
        item_type: ImpressionItemType,
        supplier_profile_id: Optional[UUIDType] = None,
    ) -> None:
        self.rail = rail
        self.position = position
        self.item_id = item_id
        self.item_type = item_type
        self.supplier_profile_id = supplier_profile_id


class ImpressionRepository:
    """Every read and write of feed_impressions."""

    # -----------------------------------------------------------------
    # Writes
    # -----------------------------------------------------------------

    @staticmethod
    def bump(
        business_id: UUIDType,
        rows: Sequence[ImpressionRow],
        *,
        column: str,
        on: Optional[date] = None,
    ) -> int:
        """Increment `column` by one for each row, inserting if absent.

        ONE STATEMENT FOR THE WHOLE FEED. A hundred cards is a hundred
        rows, and doing this as a hundred SELECT-then-UPDATE round trips
        would make composing a feed measurably slower for the benefit of
        a counter nobody is waiting on. The whole point of writing
        through the queue is that it is cheap; a chatty implementation
        would give that back.

        THE CONFLICT TARGET IS THE GRAIN ITSELF, which is why the unique
        constraint in the model is load-bearing rather than decorative.
        Without it this silently becomes an append-only event log with
        the row count the grain decision exists to avoid.
        """
        if column not in ("delivered", "tapped"):
            # NOT A GUARD AGAINST A USER, A GUARD AGAINST A TYPO. The
            # name is interpolated into the update clause below, so an
            # unrecognised one must fail here rather than reach SQL.
            raise ValueError(f"impressions have no counter called {column!r}")
        if not rows:
            return 0

        day = on or date.today()
        table = FeedImpression.__table__

        values = [
            {
                "business_id": business_id,
                "day": day,
                "rail": row.rail,
                "position": row.position,
                "item_id": row.item_id,
                "item_type": row.item_type,
                "supplier_profile_id": row.supplier_profile_id,
                column: 1,
            }
            for row in rows
        ]

        statement = pg_insert(table).values(values)
        statement = statement.on_conflict_do_update(
            constraint="uq_feed_impressions_grain",
            set_={column: getattr(table.c, column) + 1},
        )
        db.session.execute(statement)
        db.session.commit()
        return len(values)

    # -----------------------------------------------------------------
    # Reads
    # -----------------------------------------------------------------

    @staticmethod
    def categories_considered(
        business_id: UUIDType, *, since: date
    ) -> Dict[str, int]:
        """{category: cards delivered} for products this shop was shown.

        THE ONLY READ THE DEMAND ENGINE IS ALLOWED, and the return type
        is the enforcement. A Dict[str, int] of category to count is
        structurally incapable of naming a supplier -- there is no field
        for one to hide in, so no future edit can leak one through
        without changing this signature, which is a visible act rather
        than an accident on a busy week.

        WHY NOT JUST LET demand/ QUERY THE TABLE. Because the table has
        supplier_profile_id on it, and "the engine may read this table
        but must not select that column" is a rule enforced by nobody.
        The architecture test parses imports, not columns. Returning a
        narrow shape from here is the version of the rule a machine can
        check.

        CATEGORY COMES OFF THE OFFER THAT WAS SHOWN, not off the
        catalogue product behind it. Two reasons, and the second is the
        important one. The card the shop actually looked at was
        labelled with the SUPPLIER'S category, so that is what they
        considered; and an offer may be unmatched -- product_id is
        nullable by design, because deleting a catalogue product must
        leave the offer standing rather than take the order history
        with it -- so a catalogue join would silently drop every
        unmatched card from the signal.

        THE SUPPLIER TABLE IS REACHED HERE AND ONLY HERE. community/
        may import supplier/ (explore_service already does); demand/
        may not. That is precisely why this query lives on this side of
        the wall and hands back a dictionary.
        """
        from src.domains.supplier.products.models.supplier_offer import SupplierOffer

        rows = (
            db.session.query(
                SupplierOffer.category, db.func.sum(FeedImpression.delivered)
            )
            .join(
                FeedImpression,
                FeedImpression.item_id == db.cast(SupplierOffer.id, db.String),
            )
            .filter(
                FeedImpression.business_id == business_id,
                FeedImpression.day >= since,
                FeedImpression.item_type == ImpressionItemType.PRODUCT,
                FeedImpression.is_deleted.is_(False),
            )
            .group_by(SupplierOffer.category)
            .all()
        )

        return {
            getattr(category, "value", category): int(total or 0)
            for category, total in rows
            if category is not None
        }

    @staticmethod
    def for_business(
        business_id: UUIDType, *, since: Optional[date] = None
    ) -> Iterable[FeedImpression]:
        """Raw rows, for tests and for the tuning questions in V2_19.

        DELIBERATELY NOT CALLED FROM demand/. This is the wide read --
        it carries the supplier -- and it exists so a human can answer
        "what is the tap rate at position 2 of collect-near-you" without
        writing SQL by hand.
        """
        query = db.session.query(FeedImpression).filter(
            FeedImpression.business_id == business_id,
            FeedImpression.is_deleted.is_(False),
        )
        if since is not None:
            query = query.filter(FeedImpression.day >= since)
        return query.order_by(
            FeedImpression.day, FeedImpression.rail, FeedImpression.position
        ).all()
