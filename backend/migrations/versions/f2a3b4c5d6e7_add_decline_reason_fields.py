"""add stock order decline reason fields

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-09-01 18:25:00.000000

A supplier's own structured reason (plus optional free-text details)
for declining a PENDING_SUPPLIER_APPROVAL order. Mirrors
SupplierReportReason/SupplierReport.details exactly -- see the model's
own column comments for the full reasoning.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f2a3b4c5d6e7'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("stock_orders", sa.Column("decline_reason", sa.String(length=50), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("decline_details", sa.String(length=1000), nullable=True), schema="checkout")


def downgrade():
    op.drop_column("stock_orders", "decline_details", schema="checkout")
    op.drop_column("stock_orders", "decline_reason", schema="checkout")
