"""add users.last_active_at + supplier_profiles.show_last_active

Revision ID: a7b8c9d0e123
Revises: f6e7d8c9a321
Create Date: 2026-09-07 09:10:00.000000

"When was this supplier last online" -- recorded for every role
(last_active_at), shown only when the supplier opts in
(show_last_active). See both columns' own comments for why recording
and showing are deliberately separate decisions.

last_active_at is NULL for every existing row rather than backfilled
from last_login_at: those are different facts, and inventing activity a
user never had would put a false "last seen" in front of businesses.
It fills in on their next authenticated request.

Hand-trimmed to the two new columns -- autogenerate also surfaces the
same pre-existing model/DB drift every recent focused migration has.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e123'
down_revision = 'f6e7d8c9a321'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        schema='auth',
    )
    op.add_column(
        'supplier_profiles',
        sa.Column('show_last_active', sa.Boolean(), nullable=False, server_default=sa.false()),
        schema='supplier',
    )


def downgrade():
    op.drop_column('supplier_profiles', 'show_last_active', schema='supplier')
    op.drop_column('users', 'last_active_at', schema='auth')
