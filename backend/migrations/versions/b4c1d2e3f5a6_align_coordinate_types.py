"""Make a business's coordinates the same type as a supplier's.

THE INCONSISTENCY: business_profiles.latitude/longitude were
double precision, while supplier_profiles.collection_latitude/longitude
were NUMERIC(9,6). The two are compared against each other on every
"collect near you" calculation, which is exactly the pairing where a
type mismatch is least welcome.

NUMERIC(9,6) WINS RATHER THAN FLOAT, and not because it is more
accurate in range -- double precision carries more significant digits
than either column needs. It wins because it is EXACT: six decimal
places is about 11cm, a fixed and stateable precision, where a float's
precision is a property of the value. For a coordinate somebody dropped
a pin on, "this is the number, to 11cm" is a better promise than "this
is approximately the number". It also matches the column the picker
already writes to, so both sides of the comparison now round the same
way.

NOTHING IS LOST IN THE CAST. Every value in this column came from a map
widget with far fewer than six meaningful decimals, and 9 digits of
precision covers the full ±180 range.

km_between ALREADY HANDLES BOTH, having converted Decimal to float for
the supplier side since it was written -- so no application code changes
with this migration. That is the point of doing it as a migration.

THE TEST SUITE CANNOT CATCH A MISTAKE HERE: conftest.py builds the
schema from the models with db.create_all() and never runs migrations,
so the model change alone would look fine while the real database kept
its old type. Verified against the dev database directly.

Revision ID: b4c1d2e3f5a6
Revises: 5c9e2f14a7b3
"""
from alembic import op
import sqlalchemy as sa


revision = "b4c1d2e3f5a6"
down_revision = "5c9e2f14a7b3"
branch_labels = None
depends_on = None


def upgrade():
    # USING is required: Postgres will not implicitly rewrite
    # double precision to numeric on an ALTER TYPE.
    op.alter_column(
        "business_profiles",
        "latitude",
        type_=sa.Numeric(9, 6),
        existing_type=sa.Float(),
        existing_nullable=True,
        postgresql_using="latitude::numeric(9,6)",
        schema="business",
    )
    op.alter_column(
        "business_profiles",
        "longitude",
        type_=sa.Numeric(9, 6),
        existing_type=sa.Float(),
        existing_nullable=True,
        postgresql_using="longitude::numeric(9,6)",
        schema="business",
    )


def downgrade():
    op.alter_column(
        "business_profiles",
        "latitude",
        type_=sa.Float(),
        existing_type=sa.Numeric(9, 6),
        existing_nullable=True,
        postgresql_using="latitude::double precision",
        schema="business",
    )
    op.alter_column(
        "business_profiles",
        "longitude",
        type_=sa.Float(),
        existing_type=sa.Numeric(9, 6),
        existing_nullable=True,
        postgresql_using="longitude::double precision",
        schema="business",
    )
