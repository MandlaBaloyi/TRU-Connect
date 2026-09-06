"""add supplier_pinned_products table

Revision ID: b112b25717ac
Revises: 22e95d766cf1
Create Date: 2026-09-06 17:12:49.429722

Hand-trimmed to the one new table -- autogenerate also surfaced the
same pre-existing model/DB drift every recent focused migration has
(index drops, schema-scoped enum churn); none of it belongs here.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b112b25717ac'
down_revision = '22e95d766cf1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'supplier_pinned_products',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supplier_profile_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('pin_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['supplier.products.id']),
        sa.ForeignKeyConstraint(['supplier_profile_id'], ['supplier.supplier_profiles.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('supplier_profile_id', 'product_id', name='uq_supplier_pinned_products_unique'),
        schema='supplier',
    )
    op.create_index(
        'ix_supplier_pinned_products_profile_id',
        'supplier_pinned_products',
        ['supplier_profile_id'],
        unique=False,
        schema='supplier',
    )


def downgrade():
    op.drop_index('ix_supplier_pinned_products_profile_id', table_name='supplier_pinned_products', schema='supplier')
    op.drop_table('supplier_pinned_products', schema='supplier')
