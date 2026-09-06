"""add stock order decided_at timestamp

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-09-04 21:20:00.000000

When a supplier actually approved or declined an order -- null while
still PENDING_SUPPLIER_APPROVAL. Separate from submitted_at: the gap
between the two is real information (how long a business waited),
not derivable from submitted_at alone.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd7e8f9a0b1c2'
down_revision = 'c6d7e8f9a0b1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("stock_orders", sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True), schema="checkout")


def downgrade():
    op.drop_column("stock_orders", "decided_at", schema="checkout")
