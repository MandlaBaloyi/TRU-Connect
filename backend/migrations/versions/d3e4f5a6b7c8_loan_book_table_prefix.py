"""
loan_book_table_prefix

Renames three tables and their supporting indexes/constraints/enum type
to be feature-prefixed, avoiding future ambiguity as other Business
features (Order Queue, etc.) inevitably need their own "payments"/
"entries"/"history_events" concepts inside the same shared business
schema.

    loan_entries         -> loan_book_entries
    payments              -> loan_book_payments
    loan_history_events    -> loan_book_history_events
    loan_history_event_type (enum) -> loan_book_history_event_type

customers is DELIBERATELY left unchanged -- it's a genuine shared
business-level concept, not something owned by Loan Book specifically,
and other features (Order Queue included) are expected to reference the
same customer identity rather than each maintaining their own.

Uses op.rename_table()/ALTER INDEX/ALTER TYPE -- NOT drop-and-recreate.
This preserves every existing row exactly as it is; nothing is
recreated, so there is no risk of losing data already recorded in a
real, currently-running database.

Revision ID: d3e4f5a6b7c8
"""
from alembic import op

revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade():
    # --- Tables --------------------------------------------------------
    op.rename_table("loan_entries", "loan_book_entries", schema="business")
    op.rename_table("payments", "loan_book_payments", schema="business")
    op.rename_table("loan_history_events", "loan_book_history_events", schema="business")

    # --- Indexes ---------------------------------------------------------
    op.execute("ALTER INDEX business.ix_loan_entries_business_id RENAME TO ix_loan_book_entries_business_id")
    op.execute(
        "ALTER INDEX business.ix_loan_entries_business_id_deleted "
        "RENAME TO ix_loan_book_entries_business_id_deleted"
    )
    op.execute("ALTER INDEX business.ix_loan_entries_customer_id RENAME TO ix_loan_book_entries_customer_id")
    op.execute("ALTER INDEX business.ix_payments_loan_entry_id RENAME TO ix_loan_book_payments_loan_entry_id")
    op.execute("ALTER INDEX business.ix_loan_history_business_id RENAME TO ix_loan_book_history_business_id")
    op.execute(
        "ALTER INDEX business.ix_loan_history_business_id_occurred "
        "RENAME TO ix_loan_book_history_business_id_occurred"
    )

    # --- Check constraints -----------------------------------------------
    op.execute(
        "ALTER TABLE business.loan_book_entries "
        "RENAME CONSTRAINT ck_loan_entries_positive_amount TO ck_loan_book_entries_positive_amount"
    )
    op.execute(
        "ALTER TABLE business.loan_book_payments "
        "RENAME CONSTRAINT ck_payments_positive_amount TO ck_loan_book_payments_positive_amount"
    )

    # --- Primary keys -----------------------------------------------------
    # Postgres does NOT rename these automatically on table rename --
    # functionally harmless either way, but left renamed for consistency
    # with everything else touched here.
    op.execute("ALTER TABLE business.loan_book_entries RENAME CONSTRAINT loan_entries_pkey TO loan_book_entries_pkey")
    op.execute("ALTER TABLE business.loan_book_payments RENAME CONSTRAINT payments_pkey TO loan_book_payments_pkey")
    op.execute(
        "ALTER TABLE business.loan_book_history_events "
        "RENAME CONSTRAINT loan_history_events_pkey TO loan_book_history_events_pkey"
    )

    # --- Enum type ---------------------------------------------------------
    op.execute(
        "ALTER TYPE business.loan_history_event_type RENAME TO loan_book_history_event_type"
    )


def downgrade():
    op.execute("ALTER TYPE business.loan_book_history_event_type RENAME TO loan_history_event_type")

    op.execute(
        "ALTER TABLE business.loan_book_history_events "
        "RENAME CONSTRAINT loan_book_history_events_pkey TO loan_history_events_pkey"
    )
    op.execute("ALTER TABLE business.loan_book_payments RENAME CONSTRAINT loan_book_payments_pkey TO payments_pkey")
    op.execute("ALTER TABLE business.loan_book_entries RENAME CONSTRAINT loan_book_entries_pkey TO loan_entries_pkey")

    op.execute(
        "ALTER TABLE business.loan_book_payments "
        "RENAME CONSTRAINT ck_loan_book_payments_positive_amount TO ck_payments_positive_amount"
    )
    op.execute(
        "ALTER TABLE business.loan_book_entries "
        "RENAME CONSTRAINT ck_loan_book_entries_positive_amount TO ck_loan_entries_positive_amount"
    )

    op.execute(
        "ALTER INDEX business.ix_loan_book_history_business_id_occurred "
        "RENAME TO ix_loan_history_business_id_occurred"
    )
    op.execute("ALTER INDEX business.ix_loan_book_history_business_id RENAME TO ix_loan_history_business_id")
    op.execute("ALTER INDEX business.ix_loan_book_payments_loan_entry_id RENAME TO ix_payments_loan_entry_id")
    op.execute("ALTER INDEX business.ix_loan_book_entries_customer_id RENAME TO ix_loan_entries_customer_id")
    op.execute(
        "ALTER INDEX business.ix_loan_book_entries_business_id_deleted "
        "RENAME TO ix_loan_entries_business_id_deleted"
    )
    op.execute("ALTER INDEX business.ix_loan_book_entries_business_id RENAME TO ix_loan_entries_business_id")

    op.rename_table("loan_book_history_events", "loan_history_events", schema="business")
    op.rename_table("loan_book_payments", "payments", schema="business")
    op.rename_table("loan_book_entries", "loan_entries", schema="business")