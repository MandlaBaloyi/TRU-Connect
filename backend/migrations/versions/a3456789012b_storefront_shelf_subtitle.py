"""add a subtitle to a supplier's own storefront shelves

Revision ID: a3456789012b
Revises: f2345678901a
Create Date: 2026-09-07 23:55:00.000000

A second line under a supplier-curated shelf's title -- "Stock up for
month-end" / "What sells out first after payday".

CURATED SECTIONS ONLY. The four computed sections get their subtitles
from the platform (SECTION_COPY in storefront_sections_service),
because the platform is the one making the claim: "ordered most by
businesses on TruConnect" is a statement about real order data that a
supplier must not be able to reword. A shelf is the one section where
the choice is theirs, so the explanation is theirs too.

NULLABLE, and meant to stay that way. A good shelf title often needs no
explaining, and requiring a second line would only produce filler.
"""
from alembic import op
import sqlalchemy as sa

revision = 'a3456789012b'
down_revision = 'f2345678901a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "supplier_storefront_sections",
        sa.Column("subtitle", sa.String(length=80), nullable=True),
        schema="supplier",
    )


def downgrade():
    op.drop_column("supplier_storefront_sections", "subtitle", schema="supplier")
