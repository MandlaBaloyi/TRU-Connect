"""add supplier_profiles.show_track_record

Revision ID: b8c9d0e1f234
Revises: a7b8c9d0e123
Create Date: 2026-09-07 12:05:00.000000

Lets a supplier hide their track record from businesses. Defaults TRUE
-- see the column's own comment in supplier_profile.py on why this one
defaults on where show_last_active defaults off.
"""
from alembic import op
import sqlalchemy as sa

revision = 'b8c9d0e1f234'
down_revision = 'a7b8c9d0e123'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'supplier_profiles',
        sa.Column('show_track_record', sa.Boolean(), nullable=False, server_default=sa.true()),
        schema='supplier',
    )


def downgrade():
    op.drop_column('supplier_profiles', 'show_track_record', schema='supplier')
