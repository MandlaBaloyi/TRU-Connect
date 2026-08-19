"""create inventory and inventory_settings tables

Revision ID: 59274df3b81c
Revises: 8a1da193ea92
Create Date: 2026-08-18 21:37:38.000000

HAND-WRITTEN, NOT THE RAW AUTOGENERATE OUTPUT -- same reasoning as
8a1da193ea92's own docstring: `flask db migrate` also wanted to touch
unrelated loan_book/order_book/audit_events "type changes" that are
pre-existing Alembic comparison artifacts, not real changes. This file
contains only the real change: two new tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '59274df3b81c'
down_revision = '8a1da193ea92'
branch_labels = None
depends_on = None


def upgrade():
    # NOTE: the enum type is created automatically by op.create_table
    # below (any postgresql.ENUM used as a column type triggers its own
    # CREATE TYPE as part of creating the table) -- do NOT also call
    # .create() explicitly here. Doing both was tried and produces
    # psycopg2.errors.DuplicateObject: type "low_stock_alert_channel"
    # already exists, confirmed directly against a real database.
    low_stock_alert_channel = postgresql.ENUM(
        "IN_APP", "EMAIL", name="low_stock_alert_channel", schema="supplier"
    )

    op.create_table(
        "inventory",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("quantity_reserved", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.ForeignKeyConstraint(["product_id"], ["supplier.products.id"], name="inventory_product_id_fkey"),
        sa.ForeignKeyConstraint(
            ["supplier_profile_id"], ["supplier.supplier_profiles.id"], name="inventory_supplier_profile_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="inventory_pkey"),
        sa.UniqueConstraint("product_id", name="uq_inventory_product_id"),
        schema="supplier",
    )
    op.create_index(
        "ix_inventory_supplier_profile_id", "inventory", ["supplier_profile_id"], unique=False, schema="supplier"
    )

    op.create_table(
        "inventory_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supplier_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("default_low_stock_threshold", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("low_stock_alert_channel", low_stock_alert_channel, nullable=False, server_default="IN_APP"),
        sa.ForeignKeyConstraint(
            ["supplier_profile_id"],
            ["supplier.supplier_profiles.id"],
            name="inventory_settings_supplier_profile_id_fkey",
        ),
        sa.PrimaryKeyConstraint("id", name="inventory_settings_pkey"),
        sa.UniqueConstraint("supplier_profile_id", name="uq_inventory_settings_supplier_profile_id"),
        schema="supplier",
    )


def downgrade():
    op.drop_table("inventory_settings", schema="supplier")
    op.drop_index("ix_inventory_supplier_profile_id", table_name="inventory", schema="supplier")
    op.drop_table("inventory", schema="supplier")
    postgresql.ENUM(name="low_stock_alert_channel", schema="supplier").drop(op.get_bind(), checkfirst=True)
