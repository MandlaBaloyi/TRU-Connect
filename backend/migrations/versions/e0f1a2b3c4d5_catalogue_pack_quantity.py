"""A case of 24 is not a single packet.

THE BUG THIS CLOSES, measured on the seeded catalogue:

    Doritos Chips 36g x24     7 offers    R6.00 ...... R139.50

R6.00 is one 36g bag. R139.50 is a case of twenty-four. They were the
SAME canonical product, offered to shopkeepers as alternatives to each
other, and the matcher was right to link them given what it could see:
same brand, same 36g consumer unit, nearly identical text.

pack_size.py has always read "x24" correctly and PackSize has always
carried pack_quantity. There was nowhere to PUT it -- so
_create_and_link dropped it on the way in, and _pack_agreement had
nothing to compare. This is the column, and the last of four bugs of
one family: the matcher deriving the right fact and then losing it.

EIGHT PRODUCTS AFFECTED TODAY, all the same signature: a single and a
multi-pack under one name. Doritos, Simba, Score, four kinds of milk,
two soaps.

NULL MEANS A SINGLE, and is deliberately not defaulted to 1. The
overwhelming majority of products are singles, and "nobody said" and
"explicitly one" describe the same product -- but only one of them is a
fact somebody stated, and the difference is what lets a later reader
tell an unparsed name from a parsed one.

NOTHING IS BACKFILLED. The 230 existing rows were created before this
column, from names that were parsed without it; re-deriving their pack
counts here would be doing matching work inside a migration. The
re-match that follows this change does it properly, through the same
code path every future offer takes.

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
"""
from alembic import op
import sqlalchemy as sa


revision = "e0f1a2b3c4d5"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "products",
        sa.Column("pack_quantity", sa.Integer(), nullable=True),
        schema="catalogue",
    )


def downgrade():
    op.drop_column("products", "pack_quantity", schema="catalogue")
