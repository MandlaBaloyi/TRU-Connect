"""
supplier_products_table

Revision ID: 61c383f6d763
Revises: 35a0d5d4f291
Create Date: 2026-08-15

VERIFY BEFORE RUNNING: down_revision assumes 35a0d5d4f291
(rename_connection_requests_table) is your current head.

The minimal slice of the future Catalogue domain -- see
models/product.py's own docstring for the full reasoning: this exists
now so the ordering gate agreed during architecture review
("ACTIVE connection AND at least one real product") has something
real to check, not just a hypothetical rule. Deliberately lean --
id, supplier_profile_id, name, and BaseModel's standard columns, no
price/description/images/categories yet.

supplier schema already exists (created by c06dd99faa7e).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "61c383f6d763"
down_revision = "35a0d5d4f291"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "supplier_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier.supplier_profiles.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        schema="supplier",
    )
    op.create_index(
        "ix_products_supplier_profile_id", "products", ["supplier_profile_id"], schema="supplier"
    )


def downgrade():
    op.drop_index("ix_products_supplier_profile_id", table_name="products", schema="supplier")
    op.drop_table("products", schema="supplier")
