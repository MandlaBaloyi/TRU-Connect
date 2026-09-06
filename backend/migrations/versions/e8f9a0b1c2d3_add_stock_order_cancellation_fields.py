"""add stock order cancellation fields

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-09-04 21:45:00.000000

Real cancellation, two directions: a business cancelling their own
still-PENDING order, or a supplier cancelling an already-CONFIRMED
one. cancelled_by tells the two apart; cancel_reason/cancel_details
are deliberately separate columns from decline_reason/decline_details
(a genuinely different vocabulary -- see StockOrderCancelReason's own
docstring); cancelled_at is separate from decided_at so a supplier
cancelling a confirmed order doesn't silently overwrite the real fact
that it WAS confirmed once, and when.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e8f9a0b1c2d3'
down_revision = 'd7e8f9a0b1c2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("stock_orders", sa.Column("cancelled_by", sa.String(20), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("cancel_reason", sa.String(50), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("cancel_details", sa.String(1000), nullable=True), schema="checkout")
    op.add_column(
        "stock_orders", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True), schema="checkout"
    )


def downgrade():
    op.drop_column("stock_orders", "cancelled_at", schema="checkout")
    op.drop_column("stock_orders", "cancel_details", schema="checkout")
    op.drop_column("stock_orders", "cancel_reason", schema="checkout")
    op.drop_column("stock_orders", "cancelled_by", schema="checkout")
