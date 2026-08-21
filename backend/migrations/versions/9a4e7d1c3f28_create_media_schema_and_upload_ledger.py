"""create media schema and media_upload_records table

Revision ID: 9a4e7d1c3f28
Revises: 7c8e4a2f9d16
Create Date: 2026-08-19 11:30:00.000000

New schema ("media"), same CREATE SCHEMA IF NOT EXISTS pattern every
other cross-cutting domain's first migration uses (see
c06dd99faa7e_supplier_discovery_tables.py's own docstring). Lives in
its own schema, not "supplier" -- this table will record business-role
uploads (profile photos, proof of payment) the moment those domains
exist, so it was never right to nest it under one role's own schema.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9a4e7d1c3f28'
down_revision = '7c8e4a2f9d16'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS media")

    op.create_table(
        "media_upload_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("bytes", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="media_upload_records_pkey"),
        schema="media",
    )
    op.create_index(
        "ix_media_upload_records_account_id_created_at",
        "media_upload_records",
        ["account_id", "created_at"],
        unique=False,
        schema="media",
    )


def downgrade():
    op.drop_index(
        "ix_media_upload_records_account_id_created_at", table_name="media_upload_records", schema="media"
    )
    op.drop_table("media_upload_records", schema="media")
    op.execute("DROP SCHEMA IF EXISTS media")
