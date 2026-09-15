"""Drop the two completeness columns nothing ever wrote.

business_info_complete and location_complete were Section 7 of
BusinessProfile, and they backed the Verification tab's checklist.
Nothing in the codebase has ever SET either of them, so every row that
has ever existed holds False for both -- and the frontend's own
completionCalculator already answers the same question, derived from
the data itself on every read rather than from a column somebody has
to remember to update.

Two columns holding a worse answer to a question already answered
elsewhere are a trap for the next person who trusts them. See V2_18
Part 2 for the full reasoning, and for why the other nine unused
columns on this table are deliberately NOT dropped: they cost nothing
where they are, and at least two are plausible fuel for work that has
not been designed yet. These two are different because they are
actively misleading.

ORDER MATTERS AND THIS IS LAST. The code that read these went in the
previous commits -- the payload, the type, the checklist, the tab. A
column is dropped only after the readers are already gone and proven
gone; the reverse order is a broken deploy window.

DOWNGRADE RESTORES THE SHAPE, NOT THE MEANING. The columns come back
NOT NULL DEFAULT FALSE, which is exactly the state every row was in,
because False is not a placeholder here -- it is the only value either
column has ever held.

Revision ID: d4e5f6a7b8c9
Revises: a9b8c7d6e5f4
"""
from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "a9b8c7d6e5f4"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("business_profiles", "business_info_complete", schema="business")
    op.drop_column("business_profiles", "location_complete", schema="business")


def downgrade():
    op.add_column(
        "business_profiles",
        sa.Column(
            "business_info_complete",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        schema="business",
    )
    op.add_column(
        "business_profiles",
        sa.Column(
            "location_complete",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        schema="business",
    )
