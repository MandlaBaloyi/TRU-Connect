"""create import_jobs and import_job_errors tables

Revision ID: 7c8e4a2f9d16
Revises: 3f2a9c1e7b04
Create Date: 2026-08-19 07:00:00.000000

HAND-WRITTEN, matching every other migration in this build (see
8a1da193ea92's own docstring for why raw autogenerate output isn't
used directly in this codebase).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7c8e4a2f9d16'
down_revision = '3f2a9c1e7b04'
branch_labels = None
depends_on = None


def upgrade():
    import_job_status = postgresql.ENUM(
        "UPLOADED", "VALIDATING", "PROCESSING", "COMPLETED", "FAILED",
        name="import_job_status", schema="supplier",
    )

    op.create_table(
        "import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supplier_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", import_job_status, nullable=False, server_default="UPLOADED"),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("has_images_zip", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("valid_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("images_total", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("images_matched", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failure_reason", sa.String(length=500), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["supplier_profile_id"], ["supplier.supplier_profiles.id"], name="import_jobs_supplier_profile_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="import_jobs_pkey"),
        schema="supplier",
    )
    op.create_index(
        "ix_import_jobs_supplier_profile_id", "import_jobs", ["supplier_profile_id"], unique=False, schema="supplier"
    )

    op.create_table(
        "import_job_errors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("import_job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("field", sa.String(length=50), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(
            ["import_job_id"], ["supplier.import_jobs.id"], name="import_job_errors_import_job_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="import_job_errors_pkey"),
        schema="supplier",
    )
    op.create_index(
        "ix_import_job_errors_import_job_id",
        "import_job_errors",
        ["import_job_id"],
        unique=False,
        schema="supplier",
    )


def downgrade():
    op.drop_index("ix_import_job_errors_import_job_id", table_name="import_job_errors", schema="supplier")
    op.drop_table("import_job_errors", schema="supplier")
    op.drop_index("ix_import_jobs_supplier_profile_id", table_name="import_jobs", schema="supplier")
    op.drop_table("import_jobs", schema="supplier")
    postgresql.ENUM(name="import_job_status", schema="supplier").drop(op.get_bind(), checkfirst=True)
