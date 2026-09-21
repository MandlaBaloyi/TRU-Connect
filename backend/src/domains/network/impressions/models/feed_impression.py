"""
What the feed SHOWED, and what was tapped.

WHY THIS TABLE EXISTS (V2_19 Part 1). The demand engine reads DECLARED
answers and CONFIRMED orders. It has no idea what a shopkeeper LOOKED
AT. Every number tuned across V2_15, V2_16 and V2_17 carries a comment
naming what would falsify it, and almost all of them say the same
thing -- "visible the day impressions exist":

    interleave.py       the 40% proportional rail ceiling
    tier_rules.py       TOLERANCE_KM = 2.0, the tie-break band
    tier_rules.py       ABSOLUTE_CAP_BY_TIER, the one-card steps
    velocity.py         the moving-fast window

Not one of them can currently be proved wrong. They are careful
guesses, labelled as guesses, and this table is what turns the feed
from DESIGNED into MEASURED.

IT ALSO UNBLOCKS THE ONLY REVENUE MECHANISM THAT EXISTS. The sponsored
slot is picked alphabetically and nobody can be billed for it, because
no advertiser can be shown what they got.

───────────────────────────────────────────────────────────────────────
THE GRAIN, WHICH IS THE ONE HARD DECISION

A feed render is ten sections of up to twelve cards -- roughly a
hundred. Thirty shops opening the tab three times a day is 9,000 rows a
day in development. TEN THOUSAND SHOPS IS THREE MILLION A DAY. Raw
event rows would be the largest table in the system inside a month and
would answer nothing a counter does not.

ONE ROW PER (business, day, rail, position, item), with two counters.

That bounds the table by DISTINCT COMBINATIONS rather than by traffic,
and it still answers every question the falsifiers ask:

    tap rate by rail          needs rail
    tap rate by POSITION      needs position   <- the 2km falsifier
    seen but never bought     needs item
    sponsored billing         needs supplier

POSITION IS NOT OPTIONAL. tier_rules' own falsifier is "a tap-rate gap
between the first and second card of a banded pair". Without position
that sentence is unanswerable and the band can never be argued with.

───────────────────────────────────────────────────────────────────────
"delivered", NOT "shown", AND THE NAME IS LOAD-BEARING

A card below the fold was sent and never looked at. Calling the column
"shown" would make every tap rate quietly a claim the data cannot
support. Tap rate stays meaningful as long as the denominator is
defined consistently and honestly: taps per card DELIVERED.

True "seen" needs viewport detection on the device. That is a separate
piece of work and must not be smuggled in by renaming this column.

───────────────────────────────────────────────────────────────────────
NO FOREIGN KEY ON item_id, AND THAT IS DELIBERATE

item_id is a string, not a UUID with a reference, because it holds
three different sorts of thing -- a product id, a supplier id, or a
category value from the chips row -- and because an analytics row must
never be able to block a delete or be rewritten by a cascade. What the
feed showed in March is a fact about March; a product archived in April
does not make it untrue.

It is also why the column is a plain String: a nullable UUID would make
the unique constraint useless, since NULL is not equal to NULL in
Postgres and every chip row would duplicate itself forever.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class ImpressionItemType(str, enum.Enum):
    """What sort of card this row counts.

    STORED RATHER THAN INFERRED FROM THE RAIL, because the mapping is
    not one-to-one and never was: collect-near-you and not-ordered-yet
    both carry suppliers, buy-it-again carries products, and a future
    mixed rail would carry both. Reading the type off the rail name
    would be a lookup table that silently rots every time a rail is
    added.
    """

    PRODUCT = "PRODUCT"
    SUPPLIER = "SUPPLIER"
    CATEGORY = "CATEGORY"


class FeedImpression(BaseModel):
    """One (business, day, rail, position, item) with two counters."""

    __tablename__ = "feed_impressions"
    __table_args__ = (
        # THE GRAIN, ENFORCED. Everything about this table's size
        # depends on the writer finding the existing row rather than
        # inserting a second one, so the constraint is what makes the
        # upsert correct rather than merely intended.
        db.UniqueConstraint(
            "business_id",
            "day",
            "rail",
            "position",
            "item_id",
            name="uq_feed_impressions_grain",
        ),
        # "what did this shop look at and never buy", the demand read.
        db.Index("ix_feed_impressions_business_day", "business_id", "day"),
        # "what did this advertiser get", the billing read.
        db.Index("ix_feed_impressions_supplier_day", "supplier_profile_id", "day"),
        {"schema": "network"},
    )

    business_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False
    )

    #: DATE, NOT TIMESTAMP, and that is the grain decision made
    #: concrete. An hour column would multiply the table by twenty-four
    #: to answer a question nobody has asked; a day is the unit every
    #: falsifier above is phrased in.
    day = db.Column(db.Date, nullable=False)

    #: The section id the composer used -- "buy-it-again",
    #: "collect-near-you". A STRING RATHER THAN AN ENUM because rails
    #: are added and retired by product decisions, and a migration per
    #: rail would make measuring a new one more expensive than shipping
    #: it.
    rail = db.Column(db.String(64), nullable=False)

    #: 0-BASED INDEX WITHIN THE RAIL. See the module docstring: without
    #: it, tier_rules' own stated falsifier cannot be evaluated.
    position = db.Column(db.SmallInteger, nullable=False)

    item_id = db.Column(db.String(64), nullable=False)
    item_type = db.Column(
        db.Enum(ImpressionItemType, name="impression_item_type", schema="network"),
        nullable=False,
    )

    #: WHO WOULD BE BILLED. Nullable because a category chip has no
    #: supplier behind it, and because the demand engine's read of this
    #: table must never select this column -- see
    #: repositories/impression_repository.py, which is the only file
    #: allowed to decide what leaves here.
    supplier_profile_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("supplier.supplier_profiles.id"),
        nullable=True,
    )

    #: SENT TO THE DEVICE. Not "seen" -- see the module docstring.
    delivered = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    #: OPENED. The only number the device is trusted for, because it is
    #: the only one the device is the sole witness to.
    tapped = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<FeedImpression {self.rail}[{self.position}] {self.item_id} "
            f"d={self.delivered} t={self.tapped}>"
        )
