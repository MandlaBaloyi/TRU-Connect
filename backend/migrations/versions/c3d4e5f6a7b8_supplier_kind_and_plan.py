"""Add supplier_kind and plan_tier to supplier profiles.

TWO COLUMNS THAT UNBLOCK TWO DIFFERENT THINGS (V2_17).

supplier_kind EXISTS BECAUSE "EXPLORE WHOLESALERS" NEEDS SOMETHING TO
FILTER ON, and the obvious candidate -- the business NAME -- is wrong
in both directions at once. The dev database makes it concrete:
"Qwen Wholesale" and "Lepelle Wholesalers" would match a name filter,
"Seshego Cash & Carry" is a wholesaler and would not, and a retailer
trading as "Wholesale Beauty Supplies" would be listed having done
nothing wrong. A screen that can be entered by renaming a business is
a keyword search, not a filter.

plan_tier IS REACH, NOT PERMISSION (V2_16). A FREE verified supplier
stays findable, orderable and present in every earned rail their stock
belongs in. Nothing in demand/ may ever read this column; the
architecture test that keeps the demand engine supplier-blind is what
stops the feed becoming an auction.

DEFAULTS ARE THE HONEST STATE FOR EVERY EXISTING ROW. Every supplier
in the database today is UNSPECIFIED and FREE, and both are true
statements rather than placeholders -- which is why nothing is
backfilled.

server_default IS LOAD-BEARING on both. The columns are NOT NULL and
the tables are not empty, so without it this ALTER fails outright:
existing rows would need a value nobody has given them. The model's
`default=` fills rows PYTHON creates; this fills the ones already
there.

NAME == VALUE ON BOTH ENUMS, matching SupplierIngestionMode. SQLAlchemy
persists a member's NAME to Postgres rather than its .value, and this
project has already had to correct a Postgres enum for exactly that
mismatch (ConnectionRequestStatus). Matching them sidesteps the class
of bug by construction.

THE TEST SUITE CANNOT CATCH A MISTAKE HERE: conftest.py builds the
schema from the models with db.create_all() and never runs a migration,
so the model change alone would look fine while the real database kept
neither column. Verified against the dev database directly.

Revision ID: c3d4e5f6a7b8
Revises: b4c1d2e3f5a6
"""
from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "b4c1d2e3f5a6"
branch_labels = None
depends_on = None


SUPPLIER_KIND = sa.Enum(
    "WHOLESALER",
    "DISTRIBUTOR",
    "MANUFACTURER",
    "RETAILER",
    "UNSPECIFIED",
    name="supplier_kind",
    schema="supplier",
)

PLAN_TIER = sa.Enum(
    "FREE",
    "PRO",
    "MAX",
    "PARTNER",
    name="supplier_plan_tier",
    schema="supplier",
)


def upgrade():
    bind = op.get_bind()
    # create_type=False on the columns below, because the enum types are
    # created explicitly here first. Letting add_column create them
    # implicitly works until a downgrade, which then leaves the type
    # behind and makes the next upgrade fail on "type already exists".
    SUPPLIER_KIND.create(bind, checkfirst=True)
    PLAN_TIER.create(bind, checkfirst=True)

    op.add_column(
        "supplier_profiles",
        sa.Column(
            "supplier_kind",
            SUPPLIER_KIND,
            nullable=False,
            server_default="UNSPECIFIED",
        ),
        schema="supplier",
    )
    op.add_column(
        "supplier_profiles",
        sa.Column(
            "plan_tier",
            PLAN_TIER,
            nullable=False,
            server_default="FREE",
        ),
        schema="supplier",
    )
    op.add_column(
        "supplier_profiles",
        sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True),
        schema="supplier",
    )

    # PARTIAL INDEX, because the selective side is the small one.
    # "Explore wholesalers" asks for one kind out of five; indexing only
    # the rows that answer it keeps the index small and serves the only
    # query that needs it. Nothing filters on plan_tier yet -- an index
    # for a query that does not exist is a write cost with no reader.
    op.create_index(
        "ix_supplier_profiles_supplier_kind",
        "supplier_profiles",
        ["supplier_kind"],
        unique=False,
        schema="supplier",
        postgresql_where=sa.text("supplier_kind <> 'UNSPECIFIED'"),
    )


def downgrade():
    op.drop_index(
        "ix_supplier_profiles_supplier_kind",
        table_name="supplier_profiles",
        schema="supplier",
    )
    op.drop_column("supplier_profiles", "plan_expires_at", schema="supplier")
    op.drop_column("supplier_profiles", "plan_tier", schema="supplier")
    op.drop_column("supplier_profiles", "supplier_kind", schema="supplier")

    # The types go too, or a later upgrade fails on "type already
    # exists" -- Postgres does not drop an enum type with its last
    # column.
    bind = op.get_bind()
    PLAN_TIER.drop(bind, checkfirst=True)
    SUPPLIER_KIND.drop(bind, checkfirst=True)
