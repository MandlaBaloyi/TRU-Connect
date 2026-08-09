"""
business_profile_table

Revision ID: a1b2c3d4e5f6
Revises: f5a6b7c8d9e0
Create Date: 2026-08-08

VERIFY BEFORE RUNNING: down_revision below assumes f5a6b7c8d9e0
(loan_book_customers_prefix) is your current head -- confirmed by
walking the actual migration files in this codebase at the time this
was written. Re-check with `flask db heads` before running if anything
else has landed since.

ONE TABLE, business.business_profiles -- one row per business
(business_id UNIQUE), not 7 separate tables. See
models/business_profile.py's own docstring for the full reasoning.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "f5a6b7c8d9e0"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TYPE business.business_profile_category AS ENUM "
               "('FOOD_BEVERAGES','CLOTHING_FASHION','BEAUTY_COSMETICS','ELECTRONICS','RETAIL','PROFESSIONAL_SERVICES','HOME_HOUSEHOLD','OTHER')")
    op.execute("CREATE TYPE business.business_profile_type AS ENUM "
               "('SOLE_TRADER','PARTNERSHIP','FAMILY_BUSINESS','REGISTERED_COMPANY','OTHER')")
    op.execute("CREATE TYPE business.business_profile_operating_model AS ENUM "
               "('HOME','SHOP','MARKET_STALL','STREET_MOBILE','ONLINE','MULTIPLE_LOCATIONS','OTHER')")
    op.execute("CREATE TYPE business.business_profile_province AS ENUM "
               "('EASTERN_CAPE','FREE_STATE','GAUTENG','KWAZULU_NATAL','LIMPOPO','MPUMALANGA','NORTHERN_CAPE','NORTH_WEST','WESTERN_CAPE')")
    op.execute("CREATE TYPE business.business_profile_employee_range AS ENUM "
               "('JUST_ME','TWO_TO_FIVE','SIX_TO_TEN','ELEVEN_TO_TWENTY','MORE_THAN_TWENTY')")
    op.execute("CREATE TYPE business.business_profile_operating_history AS ENUM "
               "('LESS_THAN_6_MONTHS','SIX_MONTHS_TO_1_YEAR','ONE_TO_2_YEARS','TWO_TO_5_YEARS','FIVE_PLUS_YEARS')")

    op.create_table(
        "business_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),

        sa.Column("business_name", sa.String(200), nullable=False),
        sa.Column("category", postgresql.ENUM(name="business_profile_category", schema="business", create_type=False), nullable=True),
        sa.Column("business_type", postgresql.ENUM(name="business_profile_type", schema="business", create_type=False), nullable=True),
        sa.Column("description", sa.String(250), nullable=True),
        sa.Column("operating_model", postgresql.ENUM(name="business_profile_operating_model", schema="business", create_type=False), nullable=True),

        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("uses_same_as_account_phone", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("uses_same_as_account_email", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("whatsapp", sa.String(20), nullable=True),
        sa.Column("whatsapp_same_as_phone", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("whatsapp_not_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("facebook", sa.String(255), nullable=True),
        sa.Column("instagram", sa.String(255), nullable=True),

        sa.Column("province", postgresql.ENUM(name="business_profile_province", schema="business", create_type=False), nullable=True),
        sa.Column("city_or_town", sa.String(120), nullable=True),
        sa.Column("physical_address", sa.String(500), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),

        sa.Column("products", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("customer_types", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("order_channels", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("payment_methods", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("operating_days", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("opening_time", sa.String(5), nullable=True),
        sa.Column("closing_time", sa.String(5), nullable=True),
        sa.Column("employee_range", postgresql.ENUM(name="business_profile_employee_range", schema="business", create_type=False), nullable=True),

        sa.Column("years_operating", postgresql.ENUM(name="business_profile_operating_history", schema="business", create_type=False), nullable=True),

        sa.Column("supplier_sources", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),

        sa.Column("business_info_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("location_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("identity_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("documents_verified", sa.Boolean(), nullable=False, server_default=sa.false()),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),

        sa.UniqueConstraint("business_id", name="uq_business_profiles_business_id"),
        schema="business",
    )
    op.create_index("ix_business_profiles_business_id", "business_profiles", ["business_id"], schema="business")


def downgrade():
    op.drop_table("business_profiles", schema="business")
    op.execute("DROP TYPE business.business_profile_operating_history")
    op.execute("DROP TYPE business.business_profile_employee_range")
    op.execute("DROP TYPE business.business_profile_province")
    op.execute("DROP TYPE business.business_profile_operating_model")
    op.execute("DROP TYPE business.business_profile_type")
    op.execute("DROP TYPE business.business_profile_category")
