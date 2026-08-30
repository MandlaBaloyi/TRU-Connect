"""create checkout schema, stock_orders and stock_order_items

Revision ID: e7f3a1c9d5b2
Revises: d4e9f2a7b1c6
Create Date: 2026-08-28 14:15:00.000000

The real, persistent cart-and-order lifecycle. See
shared/checkout/models/stock_order.py's own module docstring for the
full reasoning.

THE PARTIAL UNIQUE INDEX is the actual point of this whole migration:
Postgres itself enforces "only one CART per (business, supplier) at a
time", not just application code that a concurrent request could race
past. Built via op.execute (SQLAlchemy's own Index(postgresql_where=)
construct generates equivalent DDL, but this migration writes it
directly for a guarantee this exact SQL is what actually runs,
verified independently of the model file's own declaration).

UPPERCASE ENUM LABELS THROUGHOUT, MATCHING PYTHON MEMBER NAMES --
applying the lesson from b8e4f1a9c3d7's own real, tested failure
(confirmed directly against the real database before trusting it,
not assumed from memory): every enum in this codebase stores the
Python member NAME as the Postgres label, not the lowercase .value.
Every new enum here is deliberately defined with member name == value
(e.g. CART = "CART") specifically so this class of bug can't recur.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7f3a1c9d5b2'
down_revision = 'd4e9f2a7b1c6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS checkout")

    op.create_table(
        "stock_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column(
            "supplier_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier.supplier_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("CART", "AWAITING_PAYMENT", "SUBMITTED", "CANCELLED", name="stock_order_status", schema="checkout"),
            nullable=False,
            server_default="CART",
        ),
        sa.Column(
            "payment_method",
            sa.Enum("CASH", "PROOF_OF_PAYMENT", "PAYFAST", name="stock_order_payment_method", schema="checkout"),
            nullable=True,
        ),
        sa.Column(
            "delivery_type",
            sa.Enum("DELIVER", "COLLECT", name="stock_order_delivery_type", schema="checkout"),
            nullable=True,
        ),
        sa.Column("delivery_address_text", sa.Text(), nullable=True),
        sa.Column("total_cents", sa.Integer(), nullable=False, server_default="0"),
        schema="checkout",
    )
    op.create_index("ix_stock_orders_business_id", "stock_orders", ["business_id"], schema="checkout")
    op.create_index(
        "ix_stock_orders_supplier_profile_id", "stock_orders", ["supplier_profile_id"], schema="checkout"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_stock_orders_one_cart_per_business_supplier "
        "ON checkout.stock_orders (business_id, supplier_profile_id) "
        "WHERE status = 'CART'"
    )

    op.create_table(
        "stock_order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "stock_order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("checkout.stock_orders.id"),
            nullable=False,
        ),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier.products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price_cents_at_add_time", sa.Integer(), nullable=False),
        schema="checkout",
    )
    op.create_index(
        "ix_stock_order_items_stock_order_id", "stock_order_items", ["stock_order_id"], schema="checkout"
    )
    op.create_index(
        "uq_stock_order_items_order_product",
        "stock_order_items",
        ["stock_order_id", "product_id"],
        unique=True,
        schema="checkout",
    )


def downgrade():
    op.drop_table("stock_order_items", schema="checkout")
    op.execute("DROP INDEX checkout.uq_stock_orders_one_cart_per_business_supplier")
    op.drop_table("stock_orders", schema="checkout")
    op.execute("DROP TYPE checkout.stock_order_delivery_type")
    op.execute("DROP TYPE checkout.stock_order_payment_method")
    op.execute("DROP TYPE checkout.stock_order_status")
    op.execute("DROP SCHEMA IF EXISTS checkout CASCADE")
