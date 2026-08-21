"""create media_upload_intents table

Revision ID: 5b8f3d2a9c17
Revises: 9a4e7d1c3f28
Create Date: 2026-08-19 16:25:00.000000

Closes the orphan-upload gap identified during review: a signature
issued and genuinely uploaded to Cloudinary, but never registered
(crash, dropped connection). Lives in the "media" schema alongside
media_upload_records -- same cross-domain reasoning (see that table's
own migration docstring).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5b8f3d2a9c17'
down_revision = '9a4e7d1c3f28'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "media_upload_intents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("cloudinary_public_id", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ISSUED"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="media_upload_intents_pkey"),
        sa.UniqueConstraint("cloudinary_public_id", name="uq_media_upload_intents_cloudinary_public_id"),
        schema="media",
    )
    op.create_index(
        "ix_media_upload_intents_status_expires_at",
        "media_upload_intents",
        ["status", "expires_at"],
        unique=False,
        schema="media",
    )


def downgrade():
    op.drop_index(
        "ix_media_upload_intents_status_expires_at", table_name="media_upload_intents", schema="media"
    )
    op.drop_table("media_upload_intents", schema="media")
