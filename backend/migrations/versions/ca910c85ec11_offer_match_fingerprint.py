"""supplier_offers.match_fingerprint

A hash of what matching last saw for this offer, so a re-imported row
whose identity has not changed does no matching work at all.

NULLABLE ON PURPOSE. Every existing offer gets NULL, which correctly
means "match it again" -- the first import after this lands re-matches
everything once and stamps it, and every import after that skips the
unchanged rows. There is no backfill to write and no window where a
wrong value would be trusted.

Hand-written, and the revision id was checked against all existing ones
before being typed -- ids collide here and surface much later as
"Multiple head revisions".

Revision ID: ca910c85ec11
Revises: 90405db18b96
Create Date: 2026-09-11
"""
from alembic import op
import sqlalchemy as sa

revision = "ca910c85ec11"
down_revision = "90405db18b96"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "supplier_offers",
        sa.Column("match_fingerprint", sa.String(length=64), nullable=True),
        schema="supplier",
    )


def downgrade():
    op.drop_column("supplier_offers", "match_fingerprint", schema="supplier")
