"""
order_book_tables

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-08-06

VERIFY BEFORE RUNNING: down_revision below assumes d3e4f5a6b7c8
(loan_book_table_prefix) is still your most recent applied migration --
confirmed to be the current head at the time this was written by
walking every migration file's revision/down_revision chain in this
codebase, but re-check with `flask db heads` before running if any
other migration has landed since.

order_book_customers is Order Book's OWN table, fully independent of
Loan Book's `business.customers` -- this was explicitly requested after
review: no foreign key, no shared row, no cross-feature effect in
either direction. Loan Book's tables/files are not touched by this
migration at all.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    order_status = postgresql.ENUM(
        "pending", "completed", "cancelled",
        name="order_book_order_status", schema="business",
    )
    deletion_cause = postgresql.ENUM(
        "manual_delete", "manual_clear_completed", "auto_clear_completed", "auto_clear_cancelled",
        name="order_book_deletion_cause", schema="business",
    )
    # Not calling .create() explicitly -- SQLAlchemy creates the
    # Postgres ENUM type automatically the first time it's used as a
    # column type inside create_table() below. See loan_book_tables.py's
    # migration for the same note and the "type already exists" failure
    # this avoids.

    op.create_table(
        "order_book_customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("first_recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_transaction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deletion_reason", sa.String(500), nullable=True),
        schema="business",
    )
    op.create_index("ix_order_book_customers_business_id", "order_book_customers", ["business_id"], schema="business")
    op.create_index(
        "ix_order_book_customers_business_id_deleted", "order_book_customers", ["business_id", "is_deleted"], schema="business"
    )

    op.create_table(
        "order_book_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("business.order_book_customers.id"), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("order_number", sa.Integer(), nullable=False),
        sa.Column("status", order_status, nullable=False, server_default="pending"),
        sa.Column("total_cents", sa.BigInteger(), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deletion_reason", sa.String(500), nullable=True),
        sa.Column("deletion_cause", deletion_cause, nullable=True),
        sa.UniqueConstraint("business_id", "order_date", "order_number", name="uq_order_book_orders_business_date_number"),
        sa.CheckConstraint("total_cents >= 0", name="ck_order_book_orders_non_negative_total"),
        schema="business",
    )
    op.create_index("ix_order_book_orders_business_id", "order_book_orders", ["business_id"], schema="business")
    op.create_index(
        "ix_order_book_orders_business_id_deleted", "order_book_orders", ["business_id", "is_deleted"], schema="business"
    )
    op.create_index("ix_order_book_orders_customer_id", "order_book_orders", ["customer_id"], schema="business")
    op.create_index(
        "ix_order_book_orders_business_id_status", "order_book_orders", ["business_id", "status"], schema="business"
    )

    op.create_table(
        "order_book_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("business.order_book_orders.id"), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.BigInteger(), nullable=False),
        sa.Column("line_total_cents", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("quantity > 0", name="ck_order_book_line_items_positive_quantity"),
        sa.CheckConstraint("unit_price_cents >= 0", name="ck_order_book_line_items_non_negative_price"),
        schema="business",
    )
    op.create_index("ix_order_book_line_items_order_id", "order_book_line_items", ["order_id"], schema="business")

    history_event_type = postgresql.ENUM(
        "order_created", "order_completed", "order_cancelled", "order_deleted", "order_restored",
        "customer_created", "customer_deleted", "customer_restored",
        name="order_book_history_event_type", schema="business",
    )

    op.create_table(
        "order_book_history_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", history_event_type, nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=True),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        schema="business",
    )
    op.create_index("ix_order_book_history_business_id", "order_book_history_events", ["business_id"], schema="business")
    op.create_index(
        "ix_order_book_history_business_id_occurred",
        "order_book_history_events", ["business_id", "occurred_at"], schema="business",
    )

    auto_clear_duration = postgresql.ENUM(
        "off", "5_min", "15_min", "custom",
        name="order_book_auto_clear_duration", schema="business",
    )

    op.create_table(
        "order_book_auto_clear_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column("completed_duration", auto_clear_duration, nullable=False, server_default="off"),
        sa.Column("completed_custom_hours", sa.Float(), nullable=True),
        sa.Column("cancelled_duration", auto_clear_duration, nullable=False, server_default="off"),
        sa.Column("cancelled_custom_hours", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("business_id", name="uq_order_book_auto_clear_settings_business_id"),
        schema="business",
    )


def downgrade():
    op.drop_table("order_book_auto_clear_settings", schema="business")
    op.execute("DROP TYPE business.order_book_auto_clear_duration")
    op.drop_table("order_book_history_events", schema="business")
    op.execute("DROP TYPE business.order_book_history_event_type")
    op.drop_table("order_book_line_items", schema="business")
    op.drop_table("order_book_orders", schema="business")
    op.execute("DROP TYPE business.order_book_deletion_cause")
    op.execute("DROP TYPE business.order_book_order_status")
    op.drop_table("order_book_customers", schema="business")
