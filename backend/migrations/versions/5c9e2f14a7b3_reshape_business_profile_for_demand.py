"""Reshape the business profile around what the demand engine reads

THE FORM ASKED TWELVE QUESTIONS AND THE ENGINE COULD USE ALMOST NONE OF
THEM. Audited 2026-09-14 (docs/v2/V2_15, Book Three Part 16).

WHAT `products` WAS. It asked what a shop SELLS, from a per-category
list of adjectives -- and PRODUCT_OPTIONS_BY_CATEGORY covered three of
the eight business categories. The other five, including RETAIL (what a
spaza shop would naturally pick), fell through to
["Products", "Services", "Other"]. So the app asked a shopkeeper what
they sell and offered them the answer "Products". Not a weak signal: no
signal, and it was the strongest thing the engine was meant to read.

`buys_categories` REPLACES IT, holding ProductCategory values. Two
changes in one:
  - SELL became BUY. A salon sells haircuts and buys relaxers; only the
    second is orderable here.
  - free-ish strings became THE REAL TAXONOMY, so a declared need lands
    directly on what the catalogue and the category chips already use,
    with no mapping table to drift.

restock_rhythm AND weekly_spend_band ARE NEW and are the two questions
that let the engine be useful before a single order exists -- one tap
each. Without them it waits months of order history to guess a cadence,
and shows a R5,000 pallet to a shop that buys R800 a week.

DROPPED, because nothing read them and nothing would:
  order_channels / payment_methods  how orders and money reach THEIR
                                    customers. Real for them, invisible
                                    to the engine.
  identity_verified                 the SUPPLIER model's concepts on a
  documents_verified                business table. The curtain gates
                                    who may SELL; a business is not
                                    checked in order to shop. Neither
                                    had a backing system, and both were
                                    False on every row that ever existed.

NOW IS WHEN THIS IS FREE. Two business_profiles rows exist. Every week
of signups turns this schema change into a data migration.

THE DOWNGRADE IS HONEST ABOUT WHAT IT CANNOT DO: it restores the
columns, not the data, and it cannot remove the enum types (PostgreSQL
has no DROP VALUE) -- same note as 4b7e1a05c9d2.

Revision ID: 5c9e2f14a7b3
Revises: 4b7e1a05c9d2
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision = "5c9e2f14a7b3"
down_revision = "4b7e1a05c9d2"
branch_labels = None
depends_on = None

SCHEMA = "business"
TABLE = "business_profiles"

RESTOCK_RHYTHM = sa.Enum(
    "DAILY", "TWICE_WEEKLY", "WEEKLY", "FORTNIGHTLY", "MONTHLY", "IRREGULAR",
    name="business_profile_restock_rhythm",
    schema=SCHEMA,
)
WEEKLY_SPEND_BAND = sa.Enum(
    "UNDER_500", "R500_TO_2000", "R2000_TO_5000", "R5000_TO_10000", "OVER_10000",
    name="business_profile_weekly_spend_band",
    schema=SCHEMA,
)


def upgrade():
    bind = op.get_bind()
    RESTOCK_RHYTHM.create(bind, checkfirst=True)
    WEEKLY_SPEND_BAND.create(bind, checkfirst=True)

    op.add_column(
        TABLE,
        sa.Column(
            "buys_categories",
            ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        schema=SCHEMA,
    )
    op.add_column(
        TABLE,
        sa.Column("restock_rhythm", RESTOCK_RHYTHM, nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        TABLE,
        sa.Column("weekly_spend_band", WEEKLY_SPEND_BAND, nullable=True),
        schema=SCHEMA,
    )

    # NOT BACKFILLED FROM `products` ON PURPOSE. Its values were words
    # like "Groceries" and, for most shops, the literal string
    # "Products" -- guessing a ProductCategory from those would seed the
    # engine with invented needs, and a wrong declared need is worse
    # than none because it is indistinguishable from a real one.
    # Two rows exist; both re-answer one question.
    for column in ("products", "order_channels", "payment_methods",
                   "identity_verified", "documents_verified"):
        op.drop_column(TABLE, column, schema=SCHEMA)

    # business_info_complete counted the OLD field set, so every stored
    # value now describes fields that no longer exist. Reset rather than
    # leave it silently wrong; it recomputes on the next save.
    op.execute(f"UPDATE {SCHEMA}.{TABLE} SET business_info_complete = false")


def downgrade():
    op.add_column(TABLE, sa.Column("products", ARRAY(sa.String()), nullable=False, server_default="{}"), schema=SCHEMA)
    op.add_column(TABLE, sa.Column("order_channels", ARRAY(sa.String()), nullable=False, server_default="{}"), schema=SCHEMA)
    op.add_column(TABLE, sa.Column("payment_methods", ARRAY(sa.String()), nullable=False, server_default="{}"), schema=SCHEMA)
    op.add_column(TABLE, sa.Column("identity_verified", sa.Boolean(), nullable=False, server_default="false"), schema=SCHEMA)
    op.add_column(TABLE, sa.Column("documents_verified", sa.Boolean(), nullable=False, server_default="false"), schema=SCHEMA)

    op.drop_column(TABLE, "weekly_spend_band", schema=SCHEMA)
    op.drop_column(TABLE, "restock_rhythm", schema=SCHEMA)
    op.drop_column(TABLE, "buys_categories", schema=SCHEMA)
    # The enum TYPES are deliberately left behind: dropping them would
    # fail if anything still referenced them, and an orphaned type is
    # harmless where a failed downgrade is not.
