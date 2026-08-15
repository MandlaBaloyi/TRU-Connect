"""
photo_visibility_fields

Revision ID: 7e079a2ec638
Revises: 61c383f6d763
Create Date: 2026-08-15

VERIFY BEFORE RUNNING: down_revision assumes 61c383f6d763
(supplier_products_table) is your current head.

Agreed during architecture review: a profile photo currently only
ever reaches the account owner's own screen -- nothing shows it to the
OTHER party in a connection. This adds the real fields needed to fix
that, symmetrically on both roles:

  auth.users.profile_image_url          -- the ONE personal photo,
                                            shared across roles (see
                                            that column's own model
                                            docstring)
  {supplier,business}.business_image_url -- a business-specific image,
                                            distinct from the personal
                                            one
  {supplier,business}.visible_image_source -- PERSONAL / BUSINESS /
                                            NONE (default NONE --
                                            nothing shows until chosen)
  {supplier,business}.photo_visibility  -- EVERYONE / CONNECTIONS /
                                            NOBODY (default
                                            CONNECTIONS -- cautious
                                            default, not the widest
                                            option)

UPPERCASE enum values, same fix applied in every prior migration in
this domain -- SQLAlchemy's Enum(PyEnumClass) persists the Python
enum member's .name, never its .value.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "7e079a2ec638"
down_revision = "61c383f6d763"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("profile_image_url", sa.String(500), nullable=True), schema="auth")

    for schema in ("supplier", "business"):
        visible_image_source = postgresql.ENUM(
            "PERSONAL", "BUSINESS", "NONE", name="visible_image_source", schema=schema
        )
        visible_image_source.create(op.get_bind())
        photo_visibility = postgresql.ENUM(
            "EVERYONE", "CONNECTIONS", "NOBODY", name="photo_visibility", schema=schema
        )
        photo_visibility.create(op.get_bind())

        table = "supplier_profiles" if schema == "supplier" else "business_profiles"

        op.add_column(table, sa.Column("business_image_url", sa.String(500), nullable=True), schema=schema)
        op.add_column(
            table,
            sa.Column("visible_image_source", visible_image_source, nullable=False, server_default="NONE"),
            schema=schema,
        )
        op.add_column(
            table,
            sa.Column("photo_visibility", photo_visibility, nullable=False, server_default="CONNECTIONS"),
            schema=schema,
        )


def downgrade():
    for schema in ("supplier", "business"):
        table = "supplier_profiles" if schema == "supplier" else "business_profiles"
        op.drop_column(table, "photo_visibility", schema=schema)
        op.drop_column(table, "visible_image_source", schema=schema)
        op.drop_column(table, "business_image_url", schema=schema)
        op.execute(f"DROP TYPE IF EXISTS {schema}.photo_visibility")
        op.execute(f"DROP TYPE IF EXISTS {schema}.visible_image_source")

    op.drop_column("users", "profile_image_url", schema="auth")
