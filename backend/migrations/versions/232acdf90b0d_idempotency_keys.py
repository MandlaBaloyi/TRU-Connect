"""Store the result of a request so a retry replays it.

V2_13 §3.1. An ERP times out at fifteen seconds and retries -- which is
CORRECT, since it cannot know whether we processed the first attempt --
and without this we create a second product.

ITS OWN SCHEMA, matching how shared/media owns "media": this is
infrastructure every domain's POST endpoints use, not something the
supplier or checkout domain owns, and the schema name should say so.

THE UNIQUE CONSTRAINT IS THE CONCURRENCY CONTROL, not bookkeeping. Two
simultaneous retries race to INSERT; exactly one wins and the loser is
told the request is already in flight.

Revision ID: 232acdf90b0d
Revises: e6efcc9b331a
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "232acdf90b0d"
down_revision = "e6efcc9b331a"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS idempotency")
    op.create_table(
        "idempotency_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_body", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("key", "user_id", name="uq_idempotency_key_user"),
        schema="idempotency",
    )
    op.create_index(
        "ix_idempotency_keys_expires_at", "idempotency_keys",
        ["expires_at"], schema="idempotency",
    )


def downgrade():
    op.drop_table("idempotency_keys", schema="idempotency")
