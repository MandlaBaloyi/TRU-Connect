"""create platform notifications table

Revision ID: e1f2a3b4c5d6
Revises: d5e6f7a8b9c0
Create Date: 2026-09-01 06:15:00.000000

The real, persisted table shared/notifications' publish mechanism
writes to. See Notification model's own docstring for the full
"deliberately generic, no real FK into whatever it's about" reasoning.

Creates the "platform" schema itself -- checked directly, and it
genuinely doesn't exist yet, same class of gap already found and fixed
for "business" a few migrations back (every other domain schema
creates itself in its own first migration; this one, apparently,
never had one before now).
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'd5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS platform")

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.String(length=500), nullable=False),
        sa.Column("related_entity_type", sa.String(length=50), nullable=True),
        sa.Column("related_entity_id", sa.String(length=100), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="platform",
    )
    op.create_index(
        "ix_notifications_recipient_user_id", "notifications", ["recipient_user_id"], schema="platform"
    )
    op.create_index("ix_notifications_category", "notifications", ["category"], schema="platform")


def downgrade():
    op.drop_index("ix_notifications_category", table_name="notifications", schema="platform")
    op.drop_index("ix_notifications_recipient_user_id", table_name="notifications", schema="platform")
    op.drop_table("notifications", schema="platform")
