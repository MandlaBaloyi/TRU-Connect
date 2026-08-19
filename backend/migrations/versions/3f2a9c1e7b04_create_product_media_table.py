"""create product_media table

Revision ID: 3f2a9c1e7b04
Revises: 59274df3b81c
Create Date: 2026-08-18 22:00:00.000000

HAND-WRITTEN, matching every other migration in this Phase (see
8a1da193ea92 and 59274df3b81c's own docstrings for why raw autogenerate
output isn't used directly in this codebase).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3f2a9c1e7b04'
down_revision = '59274df3b81c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_media",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cloudinary_public_id", sa.String(length=500), nullable=False),
        sa.Column("secure_url", sa.String(length=1000), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False, server_default="image"),
        sa.Column("format", sa.String(length=20), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("bytes", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("scan_status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("scan_provider", sa.String(length=50), nullable=True),
        sa.Column("scan_result", sa.String(length=500), nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["supplier.products.id"], name="product_media_product_id_fkey"),
        sa.PrimaryKeyConstraint("id", name="product_media_pkey"),
        sa.UniqueConstraint("cloudinary_public_id", name="uq_product_media_cloudinary_public_id"),
        schema="supplier",
    )
    op.create_index(
        "ix_product_media_product_id", "product_media", ["product_id"], unique=False, schema="supplier"
    )
    op.create_index(
        "ix_product_media_scan_status", "product_media", ["scan_status"], unique=False, schema="supplier"
    )


def downgrade():
    op.drop_index("ix_product_media_scan_status", table_name="product_media", schema="supplier")
    op.drop_index("ix_product_media_product_id", table_name="product_media", schema="supplier")
    op.drop_table("product_media", schema="supplier")
