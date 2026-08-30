"""add product_id to supplier_reports

Revision ID: d4e9f2a7b1c6
Revises: c1d5e8f3a9b2
Create Date: 2026-08-26 19:00:00.000000

Adds a nullable product_id FK -- the same report mechanism now serves
two entry points: reporting a supplier generally (product_id null) and
reporting one specific product (product_id set). See SupplierReport's
own model docstring for the full reasoning.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4e9f2a7b1c6'
down_revision = 'c1d5e8f3a9b2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "supplier_reports",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier.products.id"), nullable=True),
        schema="network",
    )
    op.create_index("ix_supplier_reports_product_id", "supplier_reports", ["product_id"], schema="network")


def downgrade():
    op.drop_index("ix_supplier_reports_product_id", table_name="supplier_reports", schema="network")
    op.drop_column("supplier_reports", "product_id", schema="network")
