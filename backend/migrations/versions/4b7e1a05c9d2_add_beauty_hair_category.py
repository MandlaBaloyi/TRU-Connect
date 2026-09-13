"""Add BEAUTY_HAIR to the product category taxonomy

Hair, wigs, braids, relaxers, cosmetics and nails are one of the largest
lines in South African informal retail, and until now they had nowhere to
go but PERSONAL_CARE -- which is soap and toothpaste, bought from a
different supplier on a different rhythm. Folding the two together put a
salon's stock behind a grocery wholesaler.

DONE NOW BECAUSE IT IS FREE NOW. catalogue.products is still empty, so
this is a pure type change with no rows to backfill or reclassify. Once
suppliers have listed thousands of offers under PERSONAL_CARE, splitting
this out stops being a migration and becomes a data project.

NO DOWNGRADE IS POSSIBLE. PostgreSQL cannot remove a value from an enum
type -- the only route back is recreating the type and rewriting every
column that uses it. The downgrade is deliberately a no-op that says so
rather than a lie that appears to work.

Revision ID: 4b7e1a05c9d2
Revises: 232acdf90b0d
"""
from alembic import op

revision = "4b7e1a05c9d2"
down_revision = "232acdf90b0d"
branch_labels = None
depends_on = None


def upgrade():
    # AFTER 'PERSONAL_CARE' keeps the database's declaration order matching
    # the Python enum, so the two never have to be read side by side to
    # work out which one is authoritative.
    op.execute(
        "ALTER TYPE supplier.product_category "
        "ADD VALUE IF NOT EXISTS 'BEAUTY_HAIR' AFTER 'PERSONAL_CARE'"
    )


def downgrade():
    # Intentionally empty -- see the module docstring.
    pass
