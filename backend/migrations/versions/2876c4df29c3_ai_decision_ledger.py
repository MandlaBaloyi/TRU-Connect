"""Add platform.ai_decisions -- the AI spend and decision ledger

V2 step 6b. Every model call the platform makes, and what it cost.

WHY A TABLE AND NOT A LOG LINE. Two jobs. It ENFORCES THE BUDGET --
spend-to-date is summed from these rows before every paid call, so
AI_MONTHLY_BUDGET_CENTS is a real limit rather than an intention. And it
makes decisions ANSWERABLE: when a supplier disputes a match, someone
has to be able to say what was asked, how sure the answer was, and which
model gave it. A log file rotates away.

IN platform, NOT IN A DOMAIN, because matching needs it today,
verification needs it next, and column mapping after that. A ledger per
feature would be three budgets each believing it is the only one
spending.

NOTHING WRITES TO IT YET. The provider seam exists; matching does not
call it. Arriving dormant is the same discipline the catalogue tables
followed.

All five BaseModel columns present -- this project has shipped a
migration that omitted deleted_at and passed every test, because
conftest builds from metadata and never runs migrations.

Revision ID: 2876c4df29c3
Revises: c32c5e454643
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "2876c4df29c3"
down_revision = "c32c5e454643"
branch_labels = None
depends_on = None

_KIND = postgresql.ENUM(
    "EXTRACT", "ADJUDICATE", name="ai_decision_kind", schema="platform", create_type=False
)


def upgrade():
    _KIND.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "ai_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("feature", sa.String(length=50), nullable=False),
        sa.Column("kind", _KIND, nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=60), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cached_input_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cost_cents", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("error", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        schema="platform",
    )
    # created_at leads because the budget query is "since the start of
    # this month" and it runs before EVERY paid call.
    op.create_index("ix_ai_decisions_created_at", "ai_decisions", ["created_at"], schema="platform")
    op.create_index("ix_ai_decisions_feature", "ai_decisions", ["feature"], schema="platform")


def downgrade():
    op.drop_index("ix_ai_decisions_feature", table_name="ai_decisions", schema="platform")
    op.drop_index("ix_ai_decisions_created_at", table_name="ai_decisions", schema="platform")
    op.drop_table("ai_decisions", schema="platform")
    _KIND.drop(op.get_bind(), checkfirst=True)
