"""
loan_book_customers_prefix

Renames the last unprefixed table in the loan_book feature:

    customers -> loan_book_customers

`customers` was DELIBERATELY left unprefixed in the original
loan_book_table_prefix migration (d3e4f5a6b7c8), on the reasoning that
it was a genuine shared business-level identity other features would
reference too. That assumption no longer holds: Order Book was built
with its OWN independent `order_book_customers` table instead of
sharing this one (an explicit decision made after review -- see
order_book/models/customer.py's docstring). With nothing left actually
sharing `customers`, leaving it unprefixed was just an inconsistency
against every other feature-owned table in this schema.

VERIFY BEFORE RUNNING: down_revision below assumes e4f5a6b7c8d9
(order_book_tables) is your current head -- confirmed by reading the
actual migration files in this codebase at the time this was written,
not guessed. Re-check with `flask db heads` before running if anything
else has landed since.

Uses op.rename_table()/ALTER INDEX/ALTER TABLE ... RENAME CONSTRAINT --
NOT drop-and-recreate. Preserves every existing row exactly as-is;
nothing is recreated, so there is no risk to real data already
recorded. Same mechanism, same reasoning, as d3e4f5a6b7c8's own rename
of loan_entries/payments/loan_history_events.

NOT RENAMED, AND DOESN'T NEED TO BE: the foreign key constraint on
loan_book_entries.customer_id (still whatever Postgres auto-generated
it as, e.g. loan_entries_customer_id_fkey) keeps working correctly
through this rename -- Postgres foreign keys reference a table by its
internal identity, not by name, so a table rename never breaks an
existing FK pointing at it. Nothing on loan_book_entries needs
touching for this migration to be complete and correct.
"""
from alembic import op

revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("customers", "loan_book_customers", schema="business")

    op.execute("ALTER INDEX business.ix_customers_business_id RENAME TO ix_loan_book_customers_business_id")
    op.execute(
        "ALTER INDEX business.ix_customers_business_id_deleted "
        "RENAME TO ix_loan_book_customers_business_id_deleted"
    )

    # Primary key -- Postgres does NOT rename this automatically on
    # table rename. Functionally harmless either way; renamed here for
    # consistency with everything else touched, same call as
    # d3e4f5a6b7c8 made for the other three tables.
    op.execute("ALTER TABLE business.loan_book_customers RENAME CONSTRAINT customers_pkey TO loan_book_customers_pkey")


def downgrade():
    op.execute("ALTER TABLE business.loan_book_customers RENAME CONSTRAINT loan_book_customers_pkey TO customers_pkey")

    op.execute(
        "ALTER INDEX business.ix_loan_book_customers_business_id_deleted "
        "RENAME TO ix_customers_business_id_deleted"
    )
    op.execute("ALTER INDEX business.ix_loan_book_customers_business_id RENAME TO ix_customers_business_id")

    op.rename_table("loan_book_customers", "customers", schema="business")