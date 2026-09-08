"""Rename supplier.products to supplier.supplier_offers, add supplier capabilities

V2 step 1 (docs/v2/V2_01_MIGRATION_AND_IMPACT, Part 4).

WHY A RENAME AND NOT A NEW TABLE. supplier.products already WAS the
offer: it carries supplier_profile_id, price_cents, sku and is_archived,
none of which are properties of a product in the world -- they are
properties of one supplier's offer of it. V1 built the right table and
gave it the wrong name. So this moves no data, copies nothing, and
touches no row: it is ALTER TABLE RENAME, which is instant and
reversible.

The six inbound foreign keys need no action. Postgres tracks them by
table OID, not by name, so they follow the rename automatically. Their
CONSTRAINT names on the child tables still say "products"
(inventory_product_id_fkey and friends) and are deliberately left alone
-- they are auto-generated names on other tables, invisible to
SQLAlchemy metadata, and renaming six constraints across four schemas
to change a word nobody reads is risk without benefit.

INDEXES AND CONSTRAINTS ARE RENAMED EXPLICITLY, because ALTER TABLE
RENAME does NOT rename them -- Postgres renames only the table. Leaving
them would mean the names in SQLAlchemy metadata and the names in the
database agree only by accident, and every future `flask db migrate`
would try to "fix" the difference.

THE TEST SUITE CANNOT VERIFY THIS FILE. conftest.py builds the schema
with db.create_all() from model metadata and never runs a migration, so
a wrong migration passes every test and fails in production. That trap
has already been hit once in this project (a hand-written migration that
omitted BaseModel's deleted_at column, corrected in f2345678901a). This
one is verified by inspecting the dev database directly after applying
it.

Revision ID: b1c2d3e4f5a6
Revises: a3456789012b
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b1c2d3e4f5a6"
down_revision = "a3456789012b"
branch_labels = None
depends_on = None


# Renames applied in both directions. (old, new) -- downgrade reverses.
_INDEX_RENAMES = (
    ("ix_products_supplier_profile_id", "ix_supplier_offers_supplier_profile_id"),
    (
        "ix_products_supplier_profile_id_is_archived",
        "ix_supplier_offers_supplier_profile_id_is_archived",
    ),
)

# Renaming a UNIQUE constraint also renames its backing index, so these
# must NOT also appear in _INDEX_RENAMES above.
_CONSTRAINT_RENAMES = (
    ("uq_products_product_code", "uq_supplier_offers_product_code"),
    (
        "uq_products_supplier_profile_id_sku",
        "uq_supplier_offers_supplier_profile_id_sku",
    ),
    ("products_pkey", "supplier_offers_pkey"),
)

_INGESTION_MODE = postgresql.ENUM(
    "MANUAL",
    "CSV",
    "API",
    name="supplier_ingestion_mode",
    schema="supplier",
    create_type=False,
)


def upgrade():
    # 1. The table itself. Instant, no rewrite, no data touched.
    op.rename_table("products", "supplier_offers", schema="supplier")

    # 2. Indexes and constraints, which the rename above left behind.
    for old, new in _INDEX_RENAMES:
        op.execute(f'ALTER INDEX supplier."{old}" RENAME TO "{new}"')
    for old, new in _CONSTRAINT_RENAMES:
        op.execute(f'ALTER TABLE supplier.supplier_offers RENAME CONSTRAINT "{old}" TO "{new}"')

    # 3. Supplier capabilities. Capabilities, not a tier enum -- see the
    #    long comment on SupplierProfile.requires_connection for why.
    _INGESTION_MODE.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "supplier_profiles",
        sa.Column(
            "requires_connection",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        schema="supplier",
    )
    op.add_column(
        "supplier_profiles",
        sa.Column(
            "ingestion_mode",
            _INGESTION_MODE,
            nullable=False,
            server_default="MANUAL",
        ),
        schema="supplier",
    )


def downgrade():
    op.drop_column("supplier_profiles", "ingestion_mode", schema="supplier")
    op.drop_column("supplier_profiles", "requires_connection", schema="supplier")
    _INGESTION_MODE.drop(op.get_bind(), checkfirst=True)

    for old, new in _CONSTRAINT_RENAMES:
        op.execute(f'ALTER TABLE supplier.supplier_offers RENAME CONSTRAINT "{new}" TO "{old}"')
    for old, new in _INDEX_RENAMES:
        op.execute(f'ALTER INDEX supplier."{new}" RENAME TO "{old}"')

    op.rename_table("supplier_offers", "products", schema="supplier")
