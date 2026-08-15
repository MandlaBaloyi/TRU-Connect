"""
supplier_invitation_table

Revision ID: 2d972736bccf
Revises: c06dd99faa7e
Create Date: 2026-08-13

VERIFY BEFORE RUNNING: down_revision assumes c06dd99faa7e
(supplier_discovery_tables) is your current head. Confirm with
`flask db heads` before running if anything else has landed since.

ONE NEW TABLE, network.supplier_invitations -- file.txt Phase 2 /
FILE2.txt "PHASE 2 -- SUPPLIER INVITATION". No new schema needed
(network already exists from the previous migration).

UPPERCASE enum values (matching the fix already applied to this
migration's predecessor): SQLAlchemy's Enum(PyEnumClass) persists the
Python enum member's .name, not its lowercase .value -- confirmed the
hard way via a real insert failure while building the previous
migration in this domain. Not repeating that mistake here.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "2d972736bccf"
down_revision = "c06dd99faa7e"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    invitation_status = postgresql.ENUM(
        "PENDING", "REGISTERED", "COMPLETED",
        name="invitation_status", schema="network",
    )
    # Not calling .create() explicitly -- SQLAlchemy creates the
    # Postgres ENUM type automatically the first time it's used as a
    # column type inside create_table(), same as every other migration
    # in this codebase.

    op.create_table(
        "supplier_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column("invited_email", sa.String(255), nullable=False),
        sa.Column("ticket_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", invitation_status, nullable=False, server_default="PENDING"),
        sa.Column("invited_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        schema="network",
    )
    op.create_index(
        "ix_supplier_invitations_ticket_hash", "supplier_invitations", ["ticket_hash"], schema="network"
    )
    op.create_index(
        "ix_supplier_invitations_business_id", "supplier_invitations", ["business_id"], schema="network"
    )


def downgrade():
    op.drop_index("ix_supplier_invitations_business_id", table_name="supplier_invitations", schema="network")
    op.drop_index("ix_supplier_invitations_ticket_hash", table_name="supplier_invitations", schema="network")
    op.drop_table("supplier_invitations", schema="network")
    op.execute("DROP TYPE IF EXISTS network.invitation_status")
