"""add auth.users.business_name

Revision ID: d3c4b5a69e10
Revises: b112b25717ac
Create Date: 2026-09-06 18:20:00.000000

Hand-trimmed to the one new column -- supplier registration now makes
`businessName` MANDATORY (owner name is the optional one), and it's
carried on the users row until otp_service._seed_supplier_profile
consumes it at verification. Autogenerate also surfaces the same
pre-existing model/DB drift every recent focused migration has (index
drops, schema-scoped enum churn); none of it belongs here.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd3c4b5a69e10'
down_revision = 'b112b25717ac'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('business_name', sa.String(length=120), nullable=True),
        schema='auth',
    )


def downgrade():
    op.drop_column('users', 'business_name', schema='auth')
