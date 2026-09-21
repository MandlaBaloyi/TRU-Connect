"""What the feed showed, and what was tapped.

Every number tuned across V2_15, V2_16 and V2_17 carries a comment
naming what would falsify it, and almost all of them say the same
thing -- "visible the day impressions exist":

    interleave.py       the 40% proportional rail ceiling
    tier_rules.py       TOLERANCE_KM = 2.0, the tie-break band
    tier_rules.py       ABSOLUTE_CAP_BY_TIER, the one-card steps
    velocity.py         the moving-fast window

Not one of them can currently be proved wrong. This is the table that
turns the feed from designed into measured -- and the one that makes
the sponsored slot billable, since today nobody can be shown what they
got.

THE GRAIN IS THE WHOLE DECISION. One row per (business, day, rail,
position, item), with two counters, NOT one row per event. A feed
render is roughly a hundred cards; thirty shops opening the tab three
times a day is 9,000 rows a day in development and ten thousand shops
is three million. Counters bound the table by distinct combinations
rather than by traffic, and answer every question above that raw events
would.

THE UNIQUE CONSTRAINT IS LOAD-BEARING, not decorative. The writer
upserts through ON CONFLICT DO UPDATE against it by name; without the
constraint this silently becomes the append-only event log the grain
exists to avoid, and nothing would fail until the table was enormous.

NO FOREIGN KEY ON item_id. It holds a supplier-offer id, a supplier
id or a category value depending on the row, and an analytics row must
never block a delete or be rewritten by a cascade -- what the feed
showed in March is a fact about March.

A RETENTION POLICY IS REQUIRED BEFORE PRODUCTION and is deliberately
not in this migration. This table grows forever otherwise, and it is
behavioural data about identifiable businesses.

Revision ID: 1a9f4c7e2b83
Revises: e0f1a2b3c4d5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "1a9f4c7e2b83"
down_revision = "e0f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade():
    # CREATED EXPLICITLY, NOT LEFT TO THE COLUMN. sa.Enum inside
    # create_table would emit its own CREATE TYPE, which fails on a
    # re-run and cannot be made conditional -- the same hazard the
    # other enum-bearing migrations in this directory work around.
    item_type = postgresql.ENUM(
        "PRODUCT",
        "SUPPLIER",
        "CATEGORY",
        name="impression_item_type",
        schema="network",
        create_type=False,
    )
    item_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "feed_impressions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id"),
            nullable=False,
        ),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("rail", sa.String(length=64), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("item_id", sa.String(length=64), nullable=False),
        sa.Column("item_type", item_type, nullable=False),
        sa.Column(
            "supplier_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier.supplier_profiles.id"),
            nullable=True,
        ),
        sa.Column("delivered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tapped", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "business_id",
            "day",
            "rail",
            "position",
            "item_id",
            name="uq_feed_impressions_grain",
        ),
        schema="network",
    )

    # "what did this shop look at and never buy" -- the demand read.
    op.create_index(
        "ix_feed_impressions_business_day",
        "feed_impressions",
        ["business_id", "day"],
        schema="network",
    )
    # "what did this advertiser get" -- the billing read.
    op.create_index(
        "ix_feed_impressions_supplier_day",
        "feed_impressions",
        ["supplier_profile_id", "day"],
        schema="network",
    )


def downgrade():
    op.drop_index(
        "ix_feed_impressions_supplier_day", table_name="feed_impressions", schema="network"
    )
    op.drop_index(
        "ix_feed_impressions_business_day", table_name="feed_impressions", schema="network"
    )
    op.drop_table("feed_impressions", schema="network")
    postgresql.ENUM(name="impression_item_type", schema="network").drop(
        op.get_bind(), checkfirst=True
    )
