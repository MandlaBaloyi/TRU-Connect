"""add sku, product_code, description, compare_at_price to products

Revision ID: 9f2c6b8e14a3
Revises: 7d3f9c2b8e41
Create Date: 2026-08-24 19:25:00.000000

Adds four new columns to supplier.products (sku, product_code,
description, compare_at_price_cents) and one to
supplier.supplier_profiles (next_sku_sequence) -- see
products/algorithms/product_code_generator.py and sku_generator.py's
own docstrings for the full reasoning behind each.

sku/product_code are added NULLABLE first, backfilled for any rows
that already exist (this build's own real test data from earlier
sessions), then tightened to NOT NULL -- the standard safe sequence
for adding a required column to a table that may already have rows,
since Postgres can't retroactively invent unique values for a
brand-new NOT NULL column on its own.
"""
import secrets

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9f2c6b8e14a3'
down_revision = '7d3f9c2b8e41'
branch_labels = None
depends_on = None

_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def _generate_product_code(existing_codes: set) -> str:
    while True:
        candidate = "TRU-" + "".join(secrets.choice(_ALPHABET) for _ in range(6))
        if candidate not in existing_codes:
            existing_codes.add(candidate)
            return candidate


def upgrade():
    op.add_column("products", sa.Column("sku", sa.String(length=50), nullable=True), schema="supplier")
    op.add_column("products", sa.Column("product_code", sa.String(length=20), nullable=True), schema="supplier")
    op.add_column("products", sa.Column("description", sa.String(length=1000), nullable=True), schema="supplier")
    op.add_column(
        "products", sa.Column("compare_at_price_cents", sa.BigInteger(), nullable=True), schema="supplier"
    )
    op.add_column(
        "supplier_profiles",
        sa.Column("next_sku_sequence", sa.Integer(), nullable=False, server_default="1"),
        schema="supplier",
    )

    connection = op.get_bind()
    products_table = sa.table(
        "products",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("supplier_profile_id", postgresql.UUID(as_uuid=True)),
        sa.column("sku", sa.String),
        sa.column("product_code", sa.String),
        schema="supplier",
    )

    existing_rows = connection.execute(
        sa.select(products_table.c.id, products_table.c.supplier_profile_id).select_from(products_table)
    ).fetchall()

    existing_codes: set = set()
    per_supplier_counters: dict = {}

    for row in existing_rows:
        supplier_id = row.supplier_profile_id
        per_supplier_counters[supplier_id] = per_supplier_counters.get(supplier_id, 0) + 1
        sku_value = f"SKU-{per_supplier_counters[supplier_id]:04d}"
        product_code_value = _generate_product_code(existing_codes)

        connection.execute(
            products_table.update()
            .where(products_table.c.id == row.id)
            .values(sku=sku_value, product_code=product_code_value)
        )

    # Keep each supplier's next_sku_sequence in sync with however many
    # backfilled products they already had, so the NEXT real product
    # they create doesn't collide with one of these backfilled SKUs.
    supplier_profiles_table = sa.table(
        "supplier_profiles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("next_sku_sequence", sa.Integer),
        schema="supplier",
    )
    for supplier_id, count in per_supplier_counters.items():
        connection.execute(
            supplier_profiles_table.update()
            .where(supplier_profiles_table.c.id == supplier_id)
            .values(next_sku_sequence=count + 1)
        )

    op.alter_column("products", "sku", nullable=False, schema="supplier")
    op.alter_column("products", "product_code", nullable=False, schema="supplier")
    op.create_unique_constraint("uq_products_product_code", "products", ["product_code"], schema="supplier")
    op.create_unique_constraint(
        "uq_products_supplier_profile_id_sku", "products", ["supplier_profile_id", "sku"], schema="supplier"
    )


def downgrade():
    op.drop_constraint("uq_products_supplier_profile_id_sku", "products", schema="supplier", type_="unique")
    op.drop_constraint("uq_products_product_code", "products", schema="supplier", type_="unique")
    op.drop_column("products", "compare_at_price_cents", schema="supplier")
    op.drop_column("products", "description", schema="supplier")
    op.drop_column("products", "product_code", schema="supplier")
    op.drop_column("products", "sku", schema="supplier")
    op.drop_column("supplier_profiles", "next_sku_sequence", schema="supplier")
