"""match review evidence and provenance

Records WHY a match was decided, not only what was decided.

HAND-WRITTEN, like every migration here -- `flask db migrate` against
this database surfaces unrelated pre-existing drift, which turns a
two-column change into a review nobody can read.

REVISION ID CHECKED AGAINST EVERY EXISTING ONE before being written.
Ids here are typed by hand and have collided before (c2d3e4f5a6b7 was
used twice), surfacing much later as "Multiple head revisions".

BOTH COLUMNS ARE NOT NULL WITH SERVER DEFAULTS, deliberately. Rows
written before evidence existed get '{}' and 'SYSTEM' rather than NULL,
so every consumer handles one shape instead of two. An empty object
means "nothing was recorded"; NULL would have meant that AND "this row
predates the feature", and those become impossible to tell apart the
moment anyone queries the column.

Revision ID: 90405db18b96
Revises: a51f7fb3e75e
Create Date: 2026-09-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "90405db18b96"
down_revision = "a51f7fb3e75e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "match_reviews",
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        schema="catalogue",
    )
    op.add_column(
        "match_reviews",
        sa.Column(
            "decided_by_source",
            sa.String(length=10),
            nullable=False,
            server_default="SYSTEM",
        ),
        schema="catalogue",
    )


def downgrade():
    op.drop_column("match_reviews", "decided_by_source", schema="catalogue")
    op.drop_column("match_reviews", "evidence", schema="catalogue")
