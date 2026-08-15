"""
supplier_discovery_tables

Revision ID: c06dd99faa7e
Revises: a1b2c3d4e5f6
Create Date: 2026-08-13

VERIFY BEFORE RUNNING: down_revision below assumes a1b2c3d4e5f6
(business_profile_table) is still your most recent applied migration
-- confirmed to be the current head at the time this was written by
walking every migration file's revision/down_revision chain in this
codebase (a1b2c3d4e5f6 is the only revision nothing else names as its
down_revision). Re-check with `flask db heads` before running if
anything else has landed since.

TWO NEW SCHEMAS, TWO NEW TABLES, matching this codebase's one-schema-
per-top-level-domain convention (auth/business/security all follow
it):

  supplier.supplier_profiles      -- a supplier's own searchable
                                      identity (file.txt Phase 1).
                                      Lives in the ALREADY-RESERVED
                                      domains/supplier/supplier_profile/
                                      (empty scaffolding until now),
                                      not duplicated inside
                                      network/supplier_discovery.

  network.supplier_connection_requests
                                   -- the minimal Phase 1 slice of the
                                      future supplier_customer_
                                      relationship domain (file.txt
                                      Phase 2/3). Only PENDING is
                                      reachable this round; ACTIVE/
                                      DECLINED are modelled now so
                                      Phase 3's approval flow extends
                                      this table instead of migrating
                                      it again.

CREATE SCHEMA IF NOT EXISTS is used for both (matching
security_audit_events.py's own correct, safe pattern) rather than
assuming Postgres already has them.

ENUM types are not created explicitly via .create() -- SQLAlchemy
creates each Postgres ENUM type automatically the first time it's used
as a column type inside create_table(), same as every other migration
in this codebase (see order_book_tables.py's own note on the "type
already exists" failure this avoids).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c06dd99faa7e"
down_revision = "a1b2c3d4e5f6"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS supplier")
    op.execute("CREATE SCHEMA IF NOT EXISTS network")

    # UPPERCASE values, matching each Python enum member's NAME, not
    # its lowercase .value -- verified directly against a real insert
    # failure during testing: SQLAlchemy's Enum(PyEnumClass) persists
    # member.name by default (never .value, even for a (str, Enum)
    # mixin), and the existing auth migration already follows this
    # exact convention (sa.Enum('BUSINESS', 'VERIFIED', ... in
    # acccb39c3c86_initial_auth_domain_schema_migration.py) -- lowercase
    # here would have been a real, silent runtime bug on first insert,
    # not just a style mismatch.
    supplier_verification_status = postgresql.ENUM(
        "UNVERIFIED", "PENDING", "VERIFIED",
        name="supplier_verification_status", schema="supplier",
    )
    connection_request_status = postgresql.ENUM(
        "PENDING", "ACTIVE", "DECLINED",
        name="connection_request_status", schema="network",
    )
    # Not calling .create() explicitly -- see module docstring.

    op.create_table(
        "supplier_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column("business_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(120), nullable=True),
        sa.Column("location", sa.String(120), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("verification_status", supplier_verification_status, nullable=False, server_default="UNVERIFIED"),
        sa.Column("normalized_phone", sa.String(20), nullable=True),
        sa.Column("normalized_email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("supplier_id", name="uq_supplier_profiles_supplier_id"),
        schema="supplier",
    )
    op.create_index(
        "ix_supplier_profiles_normalized_phone", "supplier_profiles", ["normalized_phone"], schema="supplier"
    )
    op.create_index(
        "ix_supplier_profiles_normalized_email", "supplier_profiles", ["normalized_email"], schema="supplier"
    )
    op.create_index(
        "ix_supplier_profiles_business_name", "supplier_profiles", ["business_name"], schema="supplier"
    )

    op.create_table(
        "supplier_connection_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column(
            "supplier_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier.supplier_profiles.id"),
            nullable=False,
        ),
        sa.Column("status", connection_request_status, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "business_id", "supplier_profile_id", name="uq_connection_requests_business_supplier"
        ),
        schema="network",
    )
    op.create_index(
        "ix_connection_requests_business_id", "supplier_connection_requests", ["business_id"], schema="network"
    )
    op.create_index(
        "ix_connection_requests_supplier_profile_id",
        "supplier_connection_requests",
        ["supplier_profile_id"],
        schema="network",
    )


def downgrade():
    op.drop_index("ix_connection_requests_supplier_profile_id", table_name="supplier_connection_requests", schema="network")
    op.drop_index("ix_connection_requests_business_id", table_name="supplier_connection_requests", schema="network")
    op.drop_table("supplier_connection_requests", schema="network")

    op.drop_index("ix_supplier_profiles_business_name", table_name="supplier_profiles", schema="supplier")
    op.drop_index("ix_supplier_profiles_normalized_email", table_name="supplier_profiles", schema="supplier")
    op.drop_index("ix_supplier_profiles_normalized_phone", table_name="supplier_profiles", schema="supplier")
    op.drop_table("supplier_profiles", schema="supplier")

    op.execute("DROP TYPE IF EXISTS network.connection_request_status")
    op.execute("DROP TYPE IF EXISTS supplier.supplier_verification_status")
    # Schemas intentionally NOT dropped on downgrade -- if another
    # migration lands in either schema later, dropping it here would
    # be destructive beyond what this migration itself created. Same
    # conservative choice implicitly made by every other migration in
    # this codebase (none of them drop the schemas they create).
