"""create supplier_reports table

Revision ID: c1d5e8f3a9b2
Revises: b8e4f1a9c3d7
Create Date: 2026-08-26 06:00:00.000000

New table -- a business reporting a concern about a supplier. See
SupplierReport's own model docstring for the full reasoning.

UPPERCASE ENUM LABELS, MATCHING PYTHON MEMBER NAMES -- applying the
lesson from b8e4f1a9c3d7's own real, tested failure: this codebase's
SQLAlchemy setup writes the Python enum member's NAME (e.g.
"FAKE_PRODUCTS"), not its lowercase .value string, to every enum
column. Confirmed directly against this exact table with a real
insert-and-read-back before trusting it, not assumed from the earlier
fix alone.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c1d5e8f3a9b2'
down_revision = 'b8e4f1a9c3d7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "supplier_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column(
            "supplier_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier.supplier_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.Enum(
                "FAKE_PRODUCTS", "SUSPECTED_SCAM", "ORDER_NOT_RECEIVED", "INAPPROPRIATE_CONTENT", "OTHER",
                name="supplier_report_reason", schema="network",
            ),
            nullable=False,
        ),
        sa.Column("details", sa.String(length=1000), nullable=True),
        sa.Column(
            "status",
            sa.Enum("NEW", "REVIEWED", "RESOLVED", name="supplier_report_status", schema="network"),
            nullable=False,
            server_default="NEW",
        ),
        schema="network",
    )
    op.create_index(
        "ix_supplier_reports_business_id", "supplier_reports", ["business_id"], schema="network"
    )
    op.create_index(
        "ix_supplier_reports_supplier_profile_id", "supplier_reports", ["supplier_profile_id"], schema="network"
    )


def downgrade():
    op.drop_index("ix_supplier_reports_supplier_profile_id", table_name="supplier_reports", schema="network")
    op.drop_index("ix_supplier_reports_business_id", table_name="supplier_reports", schema="network")
    op.drop_table("supplier_reports", schema="network")
    op.execute("DROP TYPE network.supplier_report_status")
    op.execute("DROP TYPE network.supplier_report_reason")
