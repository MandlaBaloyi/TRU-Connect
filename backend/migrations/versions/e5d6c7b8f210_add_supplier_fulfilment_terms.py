"""add supplier fulfilment terms (offers_delivery, minimum_order_cents)

Revision ID: e5d6c7b8f210
Revises: d3c4b5a69e10
Create Date: 2026-09-06 22:20:00.000000

The two fulfilment facts a business needs BEFORE building a cart --
"do you deliver" and "what's your minimum order". Neither existed:
delivery was only ever chosen per-order by the business, with the
supplier able to decline afterwards. See the columns' own comment in
supplier_profile.py.

offers_delivery is NOT NULL with a false server_default so existing
rows backfill to the cautious answer -- a supplier who has never
touched the setting must not appear to promise delivery.
minimum_order_cents stays nullable: NULL means "no minimum", which is
genuinely different from 0.

Hand-trimmed to the two new columns -- autogenerate also surfaces the
same pre-existing model/DB drift every recent focused migration has
(index drops, schema-scoped enum churn); none of it belongs here.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e5d6c7b8f210'
down_revision = 'd3c4b5a69e10'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'supplier_profiles',
        sa.Column('offers_delivery', sa.Boolean(), nullable=False, server_default=sa.false()),
        schema='supplier',
    )
    op.add_column(
        'supplier_profiles',
        sa.Column('minimum_order_cents', sa.Integer(), nullable=True),
        schema='supplier',
    )


def downgrade():
    op.drop_column('supplier_profiles', 'minimum_order_cents', schema='supplier')
    op.drop_column('supplier_profiles', 'offers_delivery', schema='supplier')
