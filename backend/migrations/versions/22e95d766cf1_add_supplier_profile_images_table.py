"""add supplier_profile_images table

Revision ID: 22e95d766cf1
Revises: 8bad590827b2
Create Date: 2026-09-06 14:37:09.444512

Hand-trimmed: Alembic autogenerate also surfaced a lot of pre-existing
drift between the models and this dev database (unrelated index drops,
schema-scoped enum type churn, a stock_orders partial unique index).
None of that belongs to this change -- this migration only creates the
one new table and its two indexes, matching how every other focused
migration in this project stays scoped to its own feature.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '22e95d766cf1'
down_revision = '8bad590827b2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'supplier_profile_images',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supplier_profile_id', sa.UUID(), nullable=False),
        sa.Column('slot', sa.String(length=20), nullable=False),
        sa.Column('cloudinary_public_id', sa.String(length=500), nullable=False),
        sa.Column('secure_url', sa.String(length=1000), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('bytes', sa.Integer(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('scan_status', sa.String(length=20), nullable=False),
        sa.Column('scan_provider', sa.String(length=50), nullable=True),
        sa.Column('scan_result', sa.Text(), nullable=True),
        sa.Column('scanned_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['supplier_profile_id'], ['supplier.supplier_profiles.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cloudinary_public_id'),
        schema='supplier',
    )
    op.create_index(
        'ix_supplier_profile_images_profile_id',
        'supplier_profile_images',
        ['supplier_profile_id'],
        unique=False,
        schema='supplier',
    )
    op.create_index(
        'ix_supplier_profile_images_scan_status',
        'supplier_profile_images',
        ['scan_status'],
        unique=False,
        schema='supplier',
    )


def downgrade():
    op.drop_index('ix_supplier_profile_images_scan_status', table_name='supplier_profile_images', schema='supplier')
    op.drop_index('ix_supplier_profile_images_profile_id', table_name='supplier_profile_images', schema='supplier')
    op.drop_table('supplier_profile_images', schema='supplier')
