"""add supplier cover_image_url

A separate, wide/banner-style image field on SupplierProfile, distinct
from the existing business_image_url (square/circular identity photo).
Reuse of business_image_url was considered and explicitly rejected
during the Relationship Intelligence / Supplier Profile planning round
-- these are two different UI concepts, not one field wearing two
names. Same real/mock boundary as business_image_url: the column
exists now; the frontend upload flow stays mock-backed until a real
upload-session backend exists.

Revision ID: 8bad590827b2
Revises: e8f9a0b1c2d3
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = "8bad590827b2"
down_revision = "e8f9a0b1c2d3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "supplier_profiles",
        sa.Column("cover_image_url", sa.String(length=500), nullable=True),
        schema="supplier",
    )


def downgrade():
    op.drop_column("supplier_profiles", "cover_image_url", schema="supplier")
