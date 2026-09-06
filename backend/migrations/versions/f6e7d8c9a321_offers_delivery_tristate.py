"""offers_delivery becomes tri-state (NULL = supplier hasn't said)

Revision ID: f6e7d8c9a321
Revises: e5d6c7b8f210
Create Date: 2026-09-06 23:05:00.000000

Corrects e5d6c7b8f210, which added offers_delivery as NOT NULL DEFAULT
FALSE. A boolean conflates "this supplier says they don't deliver" with
"this supplier hasn't said", and both halves of that conflation are
real bugs -- see the column's own comment in supplier_profile.py.

Every existing row is set to NULL: the fulfilment-terms feature is
hours old, so no supplier has genuinely chosen "no delivery" yet. They
all backfilled to FALSE only because that was the column default, and
treating that as a real answer would put words in their mouth.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f6e7d8c9a321'
down_revision = 'e5d6c7b8f210'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'supplier_profiles',
        'offers_delivery',
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
        schema='supplier',
    )
    # Nobody has actually answered yet -- see this migration's docstring.
    op.execute("UPDATE supplier.supplier_profiles SET offers_delivery = NULL")


def downgrade():
    op.execute("UPDATE supplier.supplier_profiles SET offers_delivery = false WHERE offers_delivery IS NULL")
    op.alter_column(
        'supplier_profiles',
        'offers_delivery',
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
        schema='supplier',
    )
