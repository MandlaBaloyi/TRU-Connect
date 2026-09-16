"""Collection is three answers, not two.

REPLACES can_collect, ADDED ONE MIGRATION AGO. That column was a
nullable Boolean -- collect, or need delivery, or never asked -- and
Mandla was right that it is short by one: "maybe they do both,
sometimes they allow deliveries, sometimes they collect themselves".

Plenty of shops fetch small top-ups themselves and have the month's
bulk delivered. Storing that as "yes, I collect" would record a CHOICE
as a CONSTRAINT, and make the difference unanswerable later without
going back and asking everybody again -- which is precisely the shape
of thing a column exists to avoid.

    COLLECT   they fetch it themselves
    DELIVERY  it must come to them
    BOTH      either, depending on the order
    NULL      never asked

NULL SURVIVES AS A STATE, and stays the default for every existing row.
The reason has not changed: an optional field that gets defaulted turns
a missing answer into an invented one.

NOTHING IS MIGRATED ACROSS, and nothing needs to be: can_collect was
added hours ago, was never exposed on a shipped build, and every row in
every database holding it is NULL. A data migration here would be
ceremony over an empty column.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
"""
from alembic import op
import sqlalchemy as sa


revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None

# NAMED AND SCHEMA-QUALIFIED so create()/drop() find the same type the
# model declares. Postgres enums are database objects, not column
# attributes -- an unnamed one here would leave an orphan type behind on
# downgrade.
STOCK_COLLECTION = sa.Enum(
    "COLLECT",
    "DELIVERY",
    "BOTH",
    name="business_profile_stock_collection",
    schema="business",
)


def upgrade():
    STOCK_COLLECTION.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "business_profiles",
        # NO server_default, for the same reason can_collect had none.
        sa.Column("stock_collection", STOCK_COLLECTION, nullable=True),
        schema="business",
    )
    op.drop_column("business_profiles", "can_collect", schema="business")


def downgrade():
    op.add_column(
        "business_profiles",
        sa.Column("can_collect", sa.Boolean(), nullable=True),
        schema="business",
    )
    op.drop_column("business_profiles", "stock_collection", schema="business")
    STOCK_COLLECTION.drop(op.get_bind(), checkfirst=True)
