"""
business_profile_search_columns

Revision ID: e6b87c4271b4
Revises: 2d972736bccf
Create Date: 2026-08-14

VERIFY BEFORE RUNNING: down_revision assumes 2d972736bccf
(supplier_invitation_table) is your current head. Confirm with
`flask db heads` before running if anything else has landed since.

Adds normalized_phone/normalized_email + three indexes to the
EXISTING business.business_profiles table -- for Find Business
(network/supplier_discovery's supplier-side mirror of Find Supplier).
No new schema, no new table -- business already exists, this table
already exists, this just gives it the same search columns
supplier_profiles already has.

Nullable, no backfill in this migration: existing BusinessProfile rows
get these populated the next time their contact details are touched,
or when the owning account re-verifies (won't re-fire for already-
verified accounts). A one-off backfill script for existing rows is a
reasonable separate follow-up, not bundled into this migration.
"""
from alembic import op
import sqlalchemy as sa

revision = "e6b87c4271b4"
down_revision = "2d972736bccf"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "business_profiles",
        sa.Column("normalized_phone", sa.String(20), nullable=True),
        schema="business",
    )
    op.add_column(
        "business_profiles",
        sa.Column("normalized_email", sa.String(255), nullable=True),
        schema="business",
    )
    op.create_index(
        "ix_business_profiles_normalized_phone", "business_profiles", ["normalized_phone"], schema="business"
    )
    op.create_index(
        "ix_business_profiles_normalized_email", "business_profiles", ["normalized_email"], schema="business"
    )
    op.create_index(
        "ix_business_profiles_business_name", "business_profiles", ["business_name"], schema="business"
    )


def downgrade():
    op.drop_index("ix_business_profiles_business_name", table_name="business_profiles", schema="business")
    op.drop_index("ix_business_profiles_normalized_email", table_name="business_profiles", schema="business")
    op.drop_index("ix_business_profiles_normalized_phone", table_name="business_profiles", schema="business")
    op.drop_column("business_profiles", "normalized_email", schema="business")
    op.drop_column("business_profiles", "normalized_phone", schema="business")
