"""grow products table with category price selling_unit unit_quantity unit_measure is_archived

Revision ID: 8a1da193ea92
Revises: 7e079a2ec638
Create Date: 2026-08-18 16:19:28.839872

HAND-WRITTEN, NOT THE RAW AUTOGENERATE OUTPUT -- `flask db migrate`
produced a migration that also wanted to drop and recreate the whole
`products` table, plus a pile of unrelated enum/index "changes" on
loan_book/order_book/audit_events that are pre-existing Alembic
comparison artifacts (SQLAlchemy's generic Enum vs introspected
schema-qualified postgresql.ENUM reads as a "type change" even though
nothing about those columns actually changed). None of that belongs in
a migration named for growing the products table, so this file
contains only the real change: two new enum types and six new columns
on `supplier.products`.

Table had zero rows at migration time (pre-launch, confirmed directly
against the dev database) -- new NOT NULL columns don't need a
nullable-then-backfill-then-constrain dance here.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8a1da193ea92'
down_revision = '7e079a2ec638'
branch_labels = None
depends_on = None

PRODUCT_CATEGORY_VALUES = (
    "FOOD_GROCERY",
    "BEVERAGES",
    "SNACKS_CONFECTIONERY",
    "BAKERY",
    "DAIRY_CHILLED",
    "FRESH_PRODUCE",
    "MEAT_FROZEN",
    "HOUSEHOLD_CLEANING",
    "PERSONAL_CARE",
    "BABY_FAMILY",
    "STATIONERY_SCHOOL",
    "HARDWARE_GENERAL",
    "ELECTRONICS_ACCESSORIES",
    "PACKAGING_DISPOSABLE",
    "CLOTHING_APPAREL",
    "OTHER",
)

PRODUCT_UNIT_VALUES = (
    "EACH",
    "PACK",
    "BOX",
    "CASE",
    "BAG",
    "BOTTLE",
    "CAN",
    "DOZEN",
    "KG",
    "G",
    "L",
    "ML",
)


def upgrade():
    product_category = postgresql.ENUM(*PRODUCT_CATEGORY_VALUES, name="product_category", schema="supplier")
    product_category.create(op.get_bind(), checkfirst=True)

    product_unit = postgresql.ENUM(*PRODUCT_UNIT_VALUES, name="product_unit", schema="supplier")
    product_unit.create(op.get_bind(), checkfirst=True)

    with op.batch_alter_table("products", schema="supplier") as batch_op:
        batch_op.add_column(sa.Column("category", product_category, nullable=False))
        batch_op.add_column(sa.Column("price_cents", sa.BigInteger(), nullable=False))
        batch_op.add_column(sa.Column("selling_unit", product_unit, nullable=False))
        batch_op.add_column(sa.Column("unit_quantity", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("unit_measure", product_unit, nullable=True))
        batch_op.add_column(
            sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false"))
        )
        batch_op.create_index(
            "ix_products_supplier_profile_id_is_archived",
            ["supplier_profile_id", "is_archived"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("products", schema="supplier") as batch_op:
        batch_op.drop_index("ix_products_supplier_profile_id_is_archived")
        batch_op.drop_column("is_archived")
        batch_op.drop_column("unit_measure")
        batch_op.drop_column("unit_quantity")
        batch_op.drop_column("selling_unit")
        batch_op.drop_column("price_cents")
        batch_op.drop_column("category")

    postgresql.ENUM(name="product_unit", schema="supplier").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="product_category", schema="supplier").drop(op.get_bind(), checkfirst=True)
