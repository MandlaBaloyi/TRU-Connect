"""add stock order reminder tracking fields

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-09-03 10:00:00.000000

Two nullable timestamps letting stock_order_reminder_sweep_job.py know
whether the 24h and 3-day reminders have already fired for a given
order -- see the model's own column comments for the full reasoning.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a3b4c5d6e7f8'
down_revision = 'f2a3b4c5d6e7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "stock_orders",
        sa.Column("first_reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
        schema="checkout",
    )
    op.add_column(
        "stock_orders",
        sa.Column("second_reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
        schema="checkout",
    )


def downgrade():
    op.drop_column("stock_orders", "second_reminder_sent_at", schema="checkout")
    op.drop_column("stock_orders", "first_reminder_sent_at", schema="checkout")
