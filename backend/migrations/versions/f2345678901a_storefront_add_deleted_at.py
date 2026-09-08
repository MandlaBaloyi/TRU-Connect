"""add the missing deleted_at column to both storefront tables

Revision ID: f2345678901a
Revises: e1f234567890
Create Date: 2026-09-07 23:35:00.000000

A CORRECTION TO e1f234567890, which hand-wrote both storefront tables
and listed only four of BaseModel's five inherited columns -- id,
created_at, updated_at and is_deleted -- and silently omitted
deleted_at. Every read of supplier_storefront_sections therefore failed
with "column supplier_storefront_sections.deleted_at does not exist",
which on the supplier profile meant the whole storefront simply did not
render.

WHY THE TESTS DID NOT CATCH IT, and this is the part worth
remembering: tests build their schema from SQLAlchemy metadata via
db.create_all(), so they got all five columns and passed happily. Only
the real database, built from the migration, was short one. A
hand-written migration is invisible to a test suite that never runs
migrations -- see backend/tests/conftest.py, which says exactly this
about itself. Any future hand-written CREATE TABLE in this project must
list all five BaseModel columns, and is worth checking against a real
`flask db upgrade` rather than a green test run.
"""
from alembic import op
import sqlalchemy as sa

revision = 'f2345678901a'
down_revision = 'e1f234567890'
branch_labels = None
depends_on = None


def upgrade():
    for table in ("supplier_storefront_sections", "supplier_storefront_section_products"):
        op.add_column(
            table,
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            schema="supplier",
        )


def downgrade():
    for table in ("supplier_storefront_sections", "supplier_storefront_section_products"):
        op.drop_column(table, "deleted_at", schema="supplier")
