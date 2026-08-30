"""create stock_order_payments

Revision ID: f6a2b8c4e9d1
Revises: e7f3a1c9d5b2
Create Date: 2026-08-28 19:00:00.000000

A payment ATTEMPT against a StockOrder, kept as its own table. See
shared/checkout/models/stock_order_payment.py's own module docstring
for the full reasoning: an order and a payment are different facts,
not one fact recorded twice, and no PayFast-specific column is ever
added to stock_orders itself.

UPPERCASE ENUM LABELS THROUGHOUT, matching Python member names --
same discipline as every enum added to this codebase since
b8e4f1a9c3d7's own real, tested failure.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f6a2b8c4e9d1'
down_revision = 'e7f3a1c9d5b2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stock_order_payments",
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
        sa.Column(
            "payment_method",
            # postgresql.ENUM (dialect-specific), not the generic
            # sa.Enum -- REAL FIX after this exact migration was run
            # and failed with the same error even with create_type=
            # False set on sa.Enum: that flag isn't reliably respected
            # by the generic cross-dialect Enum type for Postgres. The
            # dialect-specific ENUM construct is the documented,
            # reliable way to reference an existing Postgres type
            # without re-issuing its own CREATE TYPE.
            postgresql.ENUM(
                "CASH", "PROOF_OF_PAYMENT", "PAYFAST",
                name="stock_order_payment_method", schema="checkout", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("INITIATED", "SUCCEEDED", "FAILED", name="stock_order_payment_status", schema="checkout"),
            nullable=False,
            server_default="INITIATED",
        ),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("platform_commission_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="ZAR"),
        sa.Column("provider_transaction_id", sa.String(length=255), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("raw_webhook_payload", sa.Text(), nullable=True),
        sa.Column("initiated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="checkout",
    )
    op.create_index(
        "ix_stock_order_payments_stock_order_id", "stock_order_payments", ["stock_order_id"], schema="checkout"
    )


def downgrade():
    op.drop_index("ix_stock_order_payments_stock_order_id", table_name="stock_order_payments", schema="checkout")
    op.drop_table("stock_order_payments", schema="checkout")
    op.execute("DROP TYPE checkout.stock_order_payment_status")
    # stock_order_payment_method is NOT dropped here -- it's a SHARED
    # type, also used by stock_orders.payment_method itself, created
    # by e7f3a1c9d5b2's own migration. Dropping it here would break
    # that column too, which belongs to a different migration's own
    # lifecycle entirely.
