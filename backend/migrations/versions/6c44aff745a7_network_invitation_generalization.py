"""
network_invitation_generalization

Revision ID: 6c44aff745a7
Revises: e6b87c4271b4
Create Date: 2026-08-14

VERIFY BEFORE RUNNING: down_revision assumes e6b87c4271b4
(business_profile_search_columns) is your current head. Confirm with
`flask db heads` before running if anything else has landed since.
ORIGINALLY chained off 2d972736bccf directly, but that revision
already had a second child (e6b87c4271b4, adding BusinessProfile's own
normalized_phone/normalized_email -- exactly the columns this
migration's own service-layer changes depend on for Find Business's
search to work), creating two heads. Re-chained after it instead of
beside it -- makes sense anyway, since this migration's reasoning
already assumes those columns exist.

TWO CHANGES, both existing tables in network schema, no new tables:

1. supplier_invitations -> network_invitations, business_id ->
   inviter_id, + invited_role column. Generalizes the invitation
   mechanism to support "supplier invites a future business" as well
   as the original "business invites a future supplier" -- doing this
   rename now, while the table holds almost no real data, rather than
   carrying a misleadingly-named column forward. Every EXISTING row
   predates the reverse direction, so invited_role backfills to
   'SUPPLIER' for all of them (the only direction that existed before
   this migration).

2. supplier_connection_requests gains initiated_by_role. Originally
   every request was business-initiated (Find Supplier); now that a
   supplier can initiate one too (Find Business), the system needs to
   know which side owes the approval. Every EXISTING row backfills to
   'BUSINESS' for the identical reason.

UPPERCASE enum values, same fix already applied twice in this domain's
prior migrations -- SQLAlchemy's Enum(PyEnumClass) persists the Python
enum member's .name, not its lowercase .value.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "6c44aff745a7"
down_revision = "e6b87c4271b4"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    # --- 1. Generalize the invitation table -----------------------------
    op.rename_table("supplier_invitations", "network_invitations", schema="network")
    op.alter_column(
        "network_invitations", "business_id", new_column_name="inviter_id", schema="network"
    )

    invited_role = postgresql.ENUM("BUSINESS", "SUPPLIER", name="invited_role", schema="network")
    invited_role.create(op.get_bind())
    op.add_column(
        "network_invitations",
        sa.Column("invited_role", invited_role, nullable=True),
        schema="network",
    )
    # Backfill -- every row predating this migration is a business
    # inviting a future supplier, the only direction that existed.
    op.execute("UPDATE network.network_invitations SET invited_role = 'SUPPLIER'")
    op.alter_column("network_invitations", "invited_role", nullable=False, schema="network")

    op.execute(
        "ALTER INDEX network.ix_supplier_invitations_ticket_hash "
        "RENAME TO ix_network_invitations_ticket_hash"
    )
    op.execute(
        "ALTER INDEX network.ix_supplier_invitations_business_id "
        "RENAME TO ix_network_invitations_inviter_id"
    )

    # --- 2. Track which side initiated a connection request -------------
    initiator_role = postgresql.ENUM("BUSINESS", "SUPPLIER", name="connection_initiator_role", schema="network")
    initiator_role.create(op.get_bind())
    op.add_column(
        "supplier_connection_requests",
        sa.Column("initiated_by_role", initiator_role, nullable=True),
        schema="network",
    )
    # Backfill -- every row predating this migration was created by
    # Find Supplier, always business-initiated.
    op.execute("UPDATE network.supplier_connection_requests SET initiated_by_role = 'BUSINESS'")
    op.alter_column("supplier_connection_requests", "initiated_by_role", nullable=False, schema="network")


def downgrade():
    op.drop_column("supplier_connection_requests", "initiated_by_role", schema="network")
    op.execute("DROP TYPE IF EXISTS network.connection_initiator_role")

    op.execute(
        "ALTER INDEX network.ix_network_invitations_inviter_id "
        "RENAME TO ix_supplier_invitations_business_id"
    )
    op.execute(
        "ALTER INDEX network.ix_network_invitations_ticket_hash "
        "RENAME TO ix_supplier_invitations_ticket_hash"
    )
    op.drop_column("network_invitations", "invited_role", schema="network")
    op.execute("DROP TYPE IF EXISTS network.invited_role")
    op.alter_column(
        "network_invitations", "inviter_id", new_column_name="business_id", schema="network"
    )
    op.rename_table("network_invitations", "supplier_invitations", schema="network")
