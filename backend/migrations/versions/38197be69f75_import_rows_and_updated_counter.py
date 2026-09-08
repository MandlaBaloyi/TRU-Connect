"""Add supplier.import_rows and import_jobs.updated_rows

V2 step 3 (docs/v2/V2_01_MIGRATION_AND_IMPACT, Part 4).

Backs the bulk-import upsert. import_rows records what became of every
row of a supplier's file -- created, updated, or failed -- so the report
can name the lines that changed instead of only counting them, and so
the preview gate and API ingestion that come later have somewhere to
land without a second staging concept.

updated_rows sits beside created_rows because "we updated 2,800 of your
existing lines" and "we added 2,800 new ones" are wildly different
outcomes. A weekly price file should read as almost all updates; if it
reads as all creations, the supplier's SKU column did not map, and
having the two numbers side by side is what makes that visible
immediately.

ALL FIVE BaseModel COLUMNS are present on import_rows: id, created_at,
updated_at, is_deleted AND deleted_at. Spelled out because this project
has shipped a migration that omitted deleted_at and passed every test --
conftest builds from model metadata and never runs migrations, so the
suite cannot catch it. Verified against the dev database after applying.

Revision ID: 38197be69f75
Revises: 9abc21f6810f
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "38197be69f75"
down_revision = "9abc21f6810f"
branch_labels = None
depends_on = None


_OUTCOME = postgresql.ENUM(
    "CREATED",
    "UPDATED",
    "FAILED",
    name="import_row_outcome",
    schema="supplier",
    create_type=False,
)


def upgrade():
    _OUTCOME.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "import_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("import_job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("supplier_sku", sa.String(length=50), nullable=True),
        sa.Column("outcome", _OUTCOME, nullable=False),
        sa.Column("supplier_offer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["import_job_id"],
            ["supplier.import_jobs.id"],
            name="fk_import_rows_import_job_id",
        ),
        # SET NULL, not cascade: an offer being deleted later must not
        # erase the history of how it got into the catalogue.
        sa.ForeignKeyConstraint(
            ["supplier_offer_id"],
            ["supplier.supplier_offers.id"],
            name="fk_import_rows_supplier_offer_id",
            ondelete="SET NULL",
        ),
        schema="supplier",
    )
    op.create_index(
        "ix_import_rows_import_job_id", "import_rows", ["import_job_id"], schema="supplier"
    )

    op.add_column(
        "import_jobs",
        sa.Column(
            "updated_rows", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        schema="supplier",
    )


def downgrade():
    op.drop_column("import_jobs", "updated_rows", schema="supplier")
    op.drop_index("ix_import_rows_import_job_id", table_name="import_rows", schema="supplier")
    op.drop_table("import_rows", schema="supplier")
    _OUTCOME.drop(op.get_bind(), checkfirst=True)
