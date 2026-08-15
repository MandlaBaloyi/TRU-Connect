"""
rename_connection_requests_table

Revision ID: 35a0d5d4f291
Revises: c410a2f2aae9
Create Date: 2026-08-15

VERIFY BEFORE RUNNING: down_revision assumes c410a2f2aae9
(connection_request_retry_history) is your current head.

Renames supplier_connection_requests -> connection_requests. Found
during an architecture review: this table's own unique constraint and
both its indexes were ALREADY correctly named
(uq_connection_requests_business_supplier,
ix_connection_requests_business_id,
ix_connection_requests_supplier_profile_id) from when the model itself
was first written -- only the table name itself was never updated to
match. The name "supplier_connection_requests" was accurate back when
only a business could request a connection TO a supplier; now that a
supplier can request one FROM a business too (initiated_by_role), the
old name describes one direction of a relationship that goes both
ways.

No index/constraint renames needed here -- see above, they were
already right.
"""
from alembic import op

revision = "35a0d5d4f291"
down_revision = "c410a2f2aae9"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("supplier_connection_requests", "connection_requests", schema="network")


def downgrade():
    op.rename_table("connection_requests", "supplier_connection_requests", schema="network")
