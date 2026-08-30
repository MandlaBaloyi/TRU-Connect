"""add supplier contact fields (whatsapp, email, tiktok, share toggle)

Revision ID: a3f7c92e6b1d
Revises: 9f2c6b8e14a3
Create Date: 2026-08-25 18:05:00.000000

Adds whatsapp_number, contact_email, tiktok_handle (all nullable --
nothing to backfill, a supplier who hasn't entered one yet simply has
nothing there) and share_contact_details (NOT NULL, server_default
false, safely backfillable for any existing rows via the default
itself -- no per-row Python logic needed, unlike the sku/product_code
migration this backend already has as precedent for when backfill
genuinely is required).
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a3f7c92e6b1d'
down_revision = '9f2c6b8e14a3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("supplier_profiles", sa.Column("whatsapp_number", sa.String(length=20), nullable=True), schema="supplier")
    op.add_column("supplier_profiles", sa.Column("contact_email", sa.String(length=255), nullable=True), schema="supplier")
    op.add_column("supplier_profiles", sa.Column("tiktok_handle", sa.String(length=100), nullable=True), schema="supplier")
    op.add_column(
        "supplier_profiles",
        sa.Column("share_contact_details", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="supplier",
    )


def downgrade():
    op.drop_column("supplier_profiles", "share_contact_details", schema="supplier")
    op.drop_column("supplier_profiles", "tiktok_handle", schema="supplier")
    op.drop_column("supplier_profiles", "contact_email", schema="supplier")
    op.drop_column("supplier_profiles", "whatsapp_number", schema="supplier")
