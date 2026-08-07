"""
loan_book_tables

Revision ID: c2d3e4f5a6b7
Revises: b1a2c3d4e5f6
Create Date: 2026-08-04

VERIFY BEFORE RUNNING: down_revision below assumes b1a2c3d4e5f6
(security audit_events) is still your most recent applied migration.
If any migration has been applied since then, update down_revision to
that migration's real revision id instead -- `flask db history` or
`flask db current` will show you the real chain.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c2d3e4f5a6b7"
down_revision = "b1a2c3d4e5f6"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customers",
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
    op.create_index("ix_customers_business_id", "customers", ["business_id"], schema="business")
    op.create_index(
        "ix_customers_business_id_deleted", "customers", ["business_id", "is_deleted"], schema="business"
    )

    op.create_table(
        "loan_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column(
            "customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("business.customers.id"), nullable=False
        ),
        sa.Column("original_amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("sale_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_settled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deletion_reason", sa.String(500), nullable=True),
        sa.CheckConstraint("original_amount_cents > 0", name="ck_loan_entries_positive_amount"),
        schema="business",
    )
    op.create_index("ix_loan_entries_business_id", "loan_entries", ["business_id"], schema="business")
    op.create_index(
        "ix_loan_entries_business_id_deleted", "loan_entries", ["business_id", "is_deleted"], schema="business"
    )
    op.create_index("ix_loan_entries_customer_id", "loan_entries", ["customer_id"], schema="business")

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "loan_entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business.loan_entries.id"),
            nullable=False,
        ),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount_cents > 0", name="ck_payments_positive_amount"),
        schema="business",
    )
    op.create_index("ix_payments_loan_entry_id", "payments", ["loan_entry_id"], schema="business")

    loan_history_event_type = postgresql.ENUM(
        "sale_created", "payment_recorded", "payment_removed", "entry_deleted", "entry_restored",
        "customer_created", "customer_deleted", "customer_restored", "receipt_viewed", "receipt_shared",
        name="loan_history_event_type", schema="business",
    )
    # NOT calling .create() explicitly here -- SQLAlchemy already creates
    # a Postgres ENUM type automatically the first time it's used as a
    # column type inside create_table() below. Calling .create() first
    # AND using it in create_table() creates the type twice, which fails
    # with "type already exists" -- caught by actually running this
    # migration against real Postgres before shipping it.

    op.create_table(
        "loan_history_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("loan_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", loan_history_event_type, nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        schema="business",
    )
    op.create_index("ix_loan_history_business_id", "loan_history_events", ["business_id"], schema="business")
    op.create_index(
        "ix_loan_history_business_id_occurred",
        "loan_history_events", ["business_id", "occurred_at"], schema="business",
    )


def downgrade():
    op.drop_table("loan_history_events", schema="business")
    op.execute("DROP TYPE business.loan_history_event_type")
    op.drop_table("payments", schema="business")
    op.drop_table("loan_entries", schema="business")
    op.drop_table("customers", schema="business")
