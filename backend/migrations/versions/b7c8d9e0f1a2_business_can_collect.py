"""Can this shop fetch its own stock?

NULLABLE ON PURPOSE, AND NULL IS NOT FALSE. Three states, not two:
they can collect, they cannot, or they have not said. The third is why
this is not a Boolean with a server_default -- defaulting an
unanswered question turns a missing answer into an invented one, and
the feed is then ranking on a hypothesis it cannot tell apart from a
fact.

    "we need more viable than hypothesis or assumptions"  -- Mandla

Every row that exists when this runs gets NULL, which is the honest
value: none of them were ever asked.

WHAT READS IT: the "Collect near you" rail, which does not render for a
shop that has said it CANNOT collect. That rail is the only one in the
feed built on the assumption that fetching your own stock is an option,
and it is worth nothing to somebody without transport. NULL and True
both leave it exactly as it was.

MIRRORS supplier.supplier_profiles.offers_delivery, which is nullable
for the same reason on the other side of the same question -- see that
column's own comment on why a supplier who has never stated their terms
must never be shown as "Collection only".

Revision ID: b7c8d9e0f1a2
Revises: d4e5f6a7b8c9
"""
from alembic import op
import sqlalchemy as sa


revision = "b7c8d9e0f1a2"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "business_profiles",
        # NO server_default. A default here would write False or True
        # into every existing row and make "never asked" unrecoverable.
        sa.Column("can_collect", sa.Boolean(), nullable=True),
        schema="business",
    )


def downgrade():
    op.drop_column("business_profiles", "can_collect", schema="business")
