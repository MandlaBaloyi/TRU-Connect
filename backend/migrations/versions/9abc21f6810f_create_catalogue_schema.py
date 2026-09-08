"""Create the catalogue schema (brands, products) and link supplier_offers to it

V2 step 2 (docs/v2/V2_01_MIGRATION_AND_IMPACT, Part 4).

THIS MIGRATION IS DORMANT ON PURPOSE. It adds two empty tables and one
nullable column, and nothing in the application reads any of them yet.
supplier_offers.product_id starts null for every existing row and an
offer with it unset behaves exactly as it did before -- which is what
lets the catalogue ship empty and fill in over time instead of needing a
flag day.

EVERY TABLE CARRIES ALL FIVE BaseModel COLUMNS: id, created_at,
updated_at, is_deleted AND deleted_at. Spelled out because this project
has already shipped a migration that omitted deleted_at and passed the
entire test suite anyway -- conftest.py builds the schema with
db.create_all() from model metadata and never runs a migration, so the
tests were checking a database no migration produced. Corrected in
f2345678901a; the discipline is to check the dev database directly after
applying, which is what was done here.

THE TAXONOMY ENUM TYPES ARE REUSED, NOT RECREATED. catalogue.products
.category and .unit_measure point at the EXISTING supplier.product_category
and supplier.product_unit types. The Python enums moved to the catalogue
domain in this step; the Postgres types deliberately did not, because
moving a type between schemas means recreating it and rewriting every
dependent column -- real risk on live data for a cosmetic gain. See
catalogue/products/models/taxonomy.py.

Revision ID: 9abc21f6810f
Revises: b1c2d3e4f5a6
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "9abc21f6810f"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


# Existing types, created by earlier migrations. create_type=False so
# Alembic references them instead of trying to CREATE TYPE again.
_CATEGORY = postgresql.ENUM(
    name="product_category", schema="supplier", create_type=False
)
_UNIT = postgresql.ENUM(name="product_unit", schema="supplier", create_type=False)


def upgrade():
    # create_all() only ever creates TABLES, never the schemas they live
    # in -- the same lesson conftest.py records for the test database.
    op.execute("CREATE SCHEMA IF NOT EXISTS catalogue")

    op.create_table(
        "brands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("mark_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("slug", name="uq_brands_slug"),
        schema="catalogue",
    )

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("normalized_name", sa.String(length=200), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category", _CATEGORY, nullable=False),
        sa.Column("unit_quantity", sa.Integer(), nullable=True),
        sa.Column("unit_measure", _UNIT, nullable=True),
        sa.Column("gtin", sa.String(length=14), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["brand_id"], ["catalogue.brands.id"], name="fk_catalogue_products_brand_id"
        ),
        sa.UniqueConstraint("gtin", name="uq_catalogue_products_gtin"),
        schema="catalogue",
    )
    op.create_index(
        "ix_catalogue_products_normalized_name",
        "products",
        ["normalized_name"],
        schema="catalogue",
    )
    op.create_index(
        "ix_catalogue_products_brand_id", "products", ["brand_id"], schema="catalogue"
    )

    # The link. Nullable, so every existing offer stays valid untouched.
    #
    # SET NULL rather than CASCADE: removing a catalogue product must
    # never delete a supplier's offer and the order history hanging off
    # it. The correct outcome is the offer falling back to unmatched.
    op.add_column(
        "supplier_offers",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="supplier",
    )
    op.create_foreign_key(
        "fk_supplier_offers_product_id",
        "supplier_offers",
        "products",
        ["product_id"],
        ["id"],
        source_schema="supplier",
        referent_schema="catalogue",
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "fk_supplier_offers_product_id",
        "supplier_offers",
        schema="supplier",
        type_="foreignkey",
    )
    op.drop_column("supplier_offers", "product_id", schema="supplier")

    op.drop_index("ix_catalogue_products_brand_id", table_name="products", schema="catalogue")
    op.drop_index(
        "ix_catalogue_products_normalized_name", table_name="products", schema="catalogue"
    )
    op.drop_table("products", schema="catalogue")
    op.drop_table("brands", schema="catalogue")

    # The schema is dropped only if empty -- RESTRICT, never CASCADE. If
    # something else has started living in it, failing loudly is the
    # correct outcome.
    op.execute("DROP SCHEMA IF EXISTS catalogue RESTRICT")
