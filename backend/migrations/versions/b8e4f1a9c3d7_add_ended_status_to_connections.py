"""add ended status and end reason to connection_requests

Revision ID: b8e4f1a9c3d7
Revises: a3f7c92e6b1d
Create Date: 2026-08-26 00:45:00.000000

Adds ENDED to connection_request_status (Postgres enum -- ALTER TYPE
... ADD VALUE, not a plain column change) plus the two new nullable
columns (ended_reason, ended_details) recording why.

UPPERCASE LABELS, MATCHING PYTHON ENUM MEMBER NAMES -- confirmed
directly against the real database before writing this: every
existing enum in this schema (photo_visibility, product_category, and
this same connection_request_status's own PENDING/ACTIVE/DECLINED)
stores the Python member NAME as the Postgres label (e.g. "PENDING"),
not the lowercase .value string ("pending") used for JSON/API
purposes. SQLAlchemy's db.Enum(SomePythonClass) uses .name by default
unless explicitly told otherwise, and that's what this whole codebase
already relies on -- a first attempt at this migration used lowercase
'ended' and failed a real end-to-end write-and-read test with
"invalid input value for enum ... ENDED" the moment the ORM tried to
insert the correctly-uppercase value Python actually sends.

Nothing in this migration USES the new enum value in the same
transaction it's added in, which is what makes this safe to run inside
Alembic's normal transactional wrapping on Postgres 12+.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b8e4f1a9c3d7'
down_revision = 'a3f7c92e6b1d'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE network.connection_request_status ADD VALUE 'ENDED'")

    connection_end_reason = sa.Enum(
        "FOUND_BETTER_SUPPLIER", "NO_LONGER_NEEDED", "BAD_EXPERIENCE", "OTHER",
        name="connection_end_reason", schema="network",
    )
    connection_end_reason.create(op.get_bind())

    op.add_column(
        "connection_requests",
        sa.Column("ended_reason", connection_end_reason, nullable=True),
        schema="network",
    )
    op.add_column(
        "connection_requests", sa.Column("ended_details", sa.String(length=500), nullable=True), schema="network"
    )


def downgrade():
    op.drop_column("connection_requests", "ended_details", schema="network")
    op.drop_column("connection_requests", "ended_reason", schema="network")
    op.execute("DROP TYPE network.connection_end_reason")
    # Postgres has no ALTER TYPE ... DROP VALUE -- removing an enum
    # value requires rebuilding the type. Rather than reproduce that
    # multi-step dance here for a downgrade path that's realistically
    # never used outside development, this leaves 'ENDED' as a valid
    # (if unused after downgrade) value on the enum. The two columns
    # that actually depended on it are still correctly removed above.
