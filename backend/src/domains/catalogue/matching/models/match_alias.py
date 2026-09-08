"""
MatchAlias -- tier 1 of the ladder, and the only part of this system
that gets better on its own.

WHAT IT IS. One row saying "this exact text means this product":

    "coke2ltpet6pk"  ->  Coca-Cola Original 2L

The next supplier who writes it that way is matched instantly, for free,
with no rules and no model call. After a few thousand suppliers this
table answers most rows before anything else runs.

WHY THIS IS THE ASSET AND THE AI IS SCAFFOLDING. Every other tier is
either a fixed rule or a rented model. This one accumulates. The rules
in algorithms/ are written once and stay the same size; the model costs
the same per row forever. Aliases compound: each confirmed match makes
the next import cheaper, permanently, and none of it can be taken away
or repriced. If the AI were switched off for good, this table would keep
working and keep growing from the free tiers alone.

DELIBERATELY GLOBAL, NOT PER-SUPPLIER. A confirmed match learned from
one supplier's file should answer the same text in everyone else's --
that sharing IS the compounding. The risk is the obvious one: a single
wrong confirmation would then be wrong for everybody. Two things bound
it. Aliases are only written from sources that are certain or
human-confirmed (see AliasSource), never from a guess. And `source` is
recorded on every row, so if one source ever proves unreliable its
aliases can be found and removed as a group rather than hunted
individually.

THE KEY IS matching_key(), NOT THE RAW TEXT. "Coca-Cola 2LT" and "2LT
COCA COLA" collapse to one key before they get here, so one alias row
covers both spellings and the table does not fill up with variants of
the same thing.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class AliasSource(str, enum.Enum):
    """Where the alias came from, kept so a bad source is revocable as a
    group. Name == value, per this codebase's enum convention.

    RULES IS ABSENT DELIBERATELY. Tier 3 produces a score, not a
    certainty, and writing its guesses back as facts would let one
    fuzzy match teach the whole platform something wrong -- the exact
    failure this table's global scope makes expensive.
    """

    #: An exact GTIN match. The only automatic source that is certain.
    BARCODE = "BARCODE"
    #: A person looked at it and said yes.
    HUMAN = "HUMAN"
    #: An import where the supplier stated the catalogue product outright.
    DECLARED = "DECLARED"


class MatchAlias(BaseModel):
    __tablename__ = "match_aliases"
    __table_args__ = (
        db.Index("ix_match_aliases_product_id", "product_id"),
        # THE LOOKUP IS BY KEY AND MUST BE UNIQUE -- one text cannot mean
        # two products. A second confirmation of the same key updates the
        # row rather than adding one, which is also what keeps times_seen
        # meaningful.
        db.UniqueConstraint("matching_key", name="uq_match_aliases_matching_key"),
        {"schema": "catalogue"},
    )

    #: normalise.matching_key() of whatever the supplier wrote.
    matching_key = db.Column(db.String(200), nullable=False)

    #: Kept for humans reading the table. NOT used for matching -- the
    #: key is. Without it a reviewer sees "coke2ltpet6pk" and has to
    #: reverse-engineer what a supplier actually typed.
    source_text = db.Column(db.String(300), nullable=False)

    product_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("catalogue.products.id", ondelete="CASCADE"),
        nullable=False,
    )

    source = db.Column(
        db.Enum(AliasSource, name="match_alias_source", schema="catalogue"), nullable=False
    )

    #: How often this alias has been hit. Not used in matching -- it is
    #: how you find out which corrections would be worth a human's time,
    #: and which stale aliases are safe to delete.
    times_seen = db.Column(db.Integer, nullable=False, default=1, server_default=db.text("1"))
