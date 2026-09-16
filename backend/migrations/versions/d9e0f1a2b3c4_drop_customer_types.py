"""Drop customer_types, and the one thing it fed.

"who do you mainly sell to -- this one I don't need it in TruConnect,
just drop the column"  -- Mandla

HE IS RIGHT, AND THE GREP AGREES. customer_types had exactly one
consumer: weighting.prefers_bulk, which turns it into a
True/False/None on ShopNeeds. And prefers_bulk is read by NOTHING --
no rail, no section, no service, no screen. It was computed on every
call and thrown away.

So this drops the column AND prefers_bulk with it. Leaving the latter
would keep a field that can only ever be None, which is the exact
shape of thing business_info_complete and the verification block were
removed for two days ago: a value nobody writes and nobody reads,
waiting to be trusted by somebody who assumes it means something.

IT WAS ALWAYS AN INDIRECT PROXY ANYWAY. "Do you sell to other
businesses" was standing in for "do you buy by the case", and those
come apart immediately -- a spaza selling to walk-ins still buys
24-packs, and a caterer selling to offices might buy singles. If bulk
preference earns its place later it should come from what a shop
ACTUALLY ORDERS -- the units on their own confirmed lines -- which is
observation rather than a declaration about somebody else.

DATA IS LOST AND THAT IS ACCEPTED. Thirty-three rows hold values here;
none of them changes anything a user can see, today or before today.
The downgrade restores the column and its default, not the contents.

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


revision = "d9e0f1a2b3c4"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("business_profiles", "customer_types", schema="business")


def downgrade():
    op.add_column(
        "business_profiles",
        sa.Column(
            "customer_types",
            ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        schema="business",
    )
