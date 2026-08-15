"""
connection_request_retry_history

Revision ID: c410a2f2aae9
Revises: 2ea418343d1b
Create Date: 2026-08-14

VERIFY BEFORE RUNNING: down_revision assumes 2ea418343d1b
(network_invitation_fk_set_null) is your current head.

Adds retry_history to supplier_connection_requests -- an array of
timestamps, one per retry attempt, used to enforce "N retries per day,
M per week" after a DECLINED request. A single counter can't do this
correctly (it can't tell "3 retries an hour apart" from "3 retries a
week apart"); a real per-attempt timestamp history is what makes a
genuine sliding-window check possible. Deliberately NOT cache-based
(unlike login lockout, src/shared/cache/cache.py) -- that cache is
explicitly documented as in-memory, single-process, resets on
restart, which is wrong for something that needs to hold state
reliably across a full week.

Defaults to an empty array, not NULL -- every existing row (all
BUSINESS-initiated so far, from before this feature existed) simply
has no retry history yet, which is the correct starting state, not a
special case to handle.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c410a2f2aae9"
down_revision = "2ea418343d1b"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "supplier_connection_requests",
        sa.Column(
            "retry_history",
            postgresql.ARRAY(sa.DateTime(timezone=True)),
            nullable=False,
            server_default="{}",
        ),
        schema="network",
    )


def downgrade():
    op.drop_column("supplier_connection_requests", "retry_history", schema="network")
