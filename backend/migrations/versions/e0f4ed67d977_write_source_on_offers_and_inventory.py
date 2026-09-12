"""Record WHICH CHANNEL wrote a supplier offer or an inventory row.

V2_13 §3.3. A supplier edits a price in the app; their ERP pushes the
old one five minutes later. Which wins? Unanswerable today, because a
price is a value with no memory of where it came from.

BACKFILLED TO 'APP' RATHER THAN NULL, and that is not a convenience.
Every row that existed before this column did WAS written by a person
in the app, because no other channel could write one -- the importer
goes through the same service. So APP is the true value, not a
placeholder, and a nullable column would invite "unknown" handling for
a state that never occurred.

ONE ENUM TYPE, TWO TABLES. Postgres enums are schema-level objects, so
the type is created once and referenced twice; create_type=False on
the second column stops Alembic emitting a duplicate CREATE TYPE.

Revision ID: e0f4ed67d977
Revises: 01cc441488c7
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e0f4ed67d977"
down_revision = "01cc441488c7"
branch_labels = None
depends_on = None

WRITE_SOURCE = postgresql.ENUM(
    "APP", "IMPORT", "API", name="write_source", schema="supplier", create_type=False
)


def upgrade():
    WRITE_SOURCE.create(op.get_bind(), checkfirst=True)

    for table in ("supplier_offers", "inventory"):
        op.add_column(
            table,
            sa.Column(
                "source",
                WRITE_SOURCE,
                nullable=False,
                server_default="APP",
            ),
            schema="supplier",
        )


def downgrade():
    op.drop_column("inventory", "source", schema="supplier")
    op.drop_column("supplier_offers", "source", schema="supplier")
    WRITE_SOURCE.drop(op.get_bind(), checkfirst=True)
