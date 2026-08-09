"""
BusinessProfile -- "My Business" backend. ONE row per business
(business_id is unique), not 7 separate tables. Unlike Loan Book's
customers/entries/payments (genuinely separate entities with their own
lifecycle and relationships to each other), the 7 sections here are all
facets of a single object -- a business has exactly one profile, not a
list of profiles. A single wide table matches that 1:1 reality; splitting
into 7 tables would just mean 7 mandatory joins to read one profile back,
for no relational benefit.

MATCHES THE FRONTEND'S types.ts FIELD-FOR-FIELD -- every column here has
a direct counterpart in BusinessProfile/BusinessDetails/ContactDetails/
BusinessLocation/TradingDetails/OperatingHistoryInfo/SupplierInfo/
VerificationStatus. Read that file's docstring for the full reasoning
behind decisions inherited here unchanged:
  - operatingModel lives once, under Location, not duplicated as a
    separate "Business operating model" field (see that file's
    "ONE FIELD CONSOLIDATION" note).
  - Verification fields are read-only from this domain's own API --
    see VerificationStatus's own note below on where they actually come
    from.

CONFIRMS EXISTING PRECEDENT: src/domains/auth/models/user.py's own
docstring already anticipated this exact table ("future BusinessProfile
... model, connected to this User by a relationship once those tables
exist") -- this is that table, not a deviation from the plan.

NOTHING HERE REACHES INTO LOAN BOOK, ORDER BOOK, OR SUPPLIER. This is
the identity layer those features may reference later (business name,
category, location) -- it never duplicates or owns their operational
data, and they never write to this table.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import ARRAY, UUID

from src.core.base_model import BaseModel
from src.extensions import db


class BusinessCategory(str, enum.Enum):
    FOOD_BEVERAGES = "FOOD_BEVERAGES"
    CLOTHING_FASHION = "CLOTHING_FASHION"
    BEAUTY_COSMETICS = "BEAUTY_COSMETICS"
    ELECTRONICS = "ELECTRONICS"
    RETAIL = "RETAIL"
    PROFESSIONAL_SERVICES = "PROFESSIONAL_SERVICES"
    HOME_HOUSEHOLD = "HOME_HOUSEHOLD"
    OTHER = "OTHER"


class BusinessType(str, enum.Enum):
    SOLE_TRADER = "SOLE_TRADER"
    PARTNERSHIP = "PARTNERSHIP"
    FAMILY_BUSINESS = "FAMILY_BUSINESS"
    REGISTERED_COMPANY = "REGISTERED_COMPANY"
    OTHER = "OTHER"


class OperatingModel(str, enum.Enum):
    HOME = "HOME"
    SHOP = "SHOP"
    MARKET_STALL = "MARKET_STALL"
    STREET_MOBILE = "STREET_MOBILE"
    ONLINE = "ONLINE"
    MULTIPLE_LOCATIONS = "MULTIPLE_LOCATIONS"
    OTHER = "OTHER"


class SouthAfricanProvince(str, enum.Enum):
    EASTERN_CAPE = "EASTERN_CAPE"
    FREE_STATE = "FREE_STATE"
    GAUTENG = "GAUTENG"
    KWAZULU_NATAL = "KWAZULU_NATAL"
    LIMPOPO = "LIMPOPO"
    MPUMALANGA = "MPUMALANGA"
    NORTHERN_CAPE = "NORTHERN_CAPE"
    NORTH_WEST = "NORTH_WEST"
    WESTERN_CAPE = "WESTERN_CAPE"


class EmployeeRange(str, enum.Enum):
    JUST_ME = "JUST_ME"
    TWO_TO_FIVE = "TWO_TO_FIVE"
    SIX_TO_TEN = "SIX_TO_TEN"
    ELEVEN_TO_TWENTY = "ELEVEN_TO_TWENTY"
    MORE_THAN_TWENTY = "MORE_THAN_TWENTY"


class OperatingHistory(str, enum.Enum):
    LESS_THAN_6_MONTHS = "LESS_THAN_6_MONTHS"
    SIX_MONTHS_TO_1_YEAR = "SIX_MONTHS_TO_1_YEAR"
    ONE_TO_2_YEARS = "ONE_TO_2_YEARS"
    TWO_TO_5_YEARS = "TWO_TO_5_YEARS"
    FIVE_PLUS_YEARS = "FIVE_PLUS_YEARS"


# CustomerType/OrderChannel/PaymentMethod/Weekday/SupplierSource are
# stored as ARRAY(String), not ARRAY(Enum) -- Postgres arrays-of-enum
# are real but add real migration/driver friction for no benefit here,
# since these values are validated at the schema layer
# (schemas/business_profile_schemas.py) against the same option lists
# the frontend's types.ts declares, not by a DB-level constraint. This
# mirrors how Order Book stores its own list-like data (line items are
# a real child table there because they need their own identity; these
# are just tag lists, not entities).


class BusinessProfile(BaseModel):
    __tablename__ = "business_profiles"
    __table_args__ = (
        db.UniqueConstraint("business_id", name="uq_business_profiles_business_id"),
        {"schema": "business"},
    )

    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)

    # --- Section 1: Business Details ---
    business_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.Enum(BusinessCategory, name="business_profile_category", schema="business"), nullable=True)
    business_type = db.Column(db.Enum(BusinessType, name="business_profile_type", schema="business"), nullable=True)
    description = db.Column(db.String(250), nullable=True)
    operating_model = db.Column(db.Enum(OperatingModel, name="business_profile_operating_model", schema="business"), nullable=True)

    # --- Section 2: Contact Details ---
    phone = db.Column(db.String(20), nullable=True)
    uses_same_as_account_phone = db.Column(db.Boolean, nullable=False, default=True)
    email = db.Column(db.String(255), nullable=True)
    uses_same_as_account_email = db.Column(db.Boolean, nullable=False, default=True)
    whatsapp = db.Column(db.String(20), nullable=True)
    whatsapp_same_as_phone = db.Column(db.Boolean, nullable=False, default=True)
    whatsapp_not_used = db.Column(db.Boolean, nullable=False, default=False)
    facebook = db.Column(db.String(255), nullable=True)
    instagram = db.Column(db.String(255), nullable=True)

    # --- Section 3: Location ---
    province = db.Column(db.Enum(SouthAfricanProvince, name="business_profile_province", schema="business"), nullable=True)
    city_or_town = db.Column(db.String(120), nullable=True)
    physical_address = db.Column(db.String(500), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    # --- Section 4: Trading Details ---
    products = db.Column(ARRAY(db.String), nullable=False, default=list)
    customer_types = db.Column(ARRAY(db.String), nullable=False, default=list)
    order_channels = db.Column(ARRAY(db.String), nullable=False, default=list)
    payment_methods = db.Column(ARRAY(db.String), nullable=False, default=list)
    operating_days = db.Column(ARRAY(db.String), nullable=False, default=list)
    opening_time = db.Column(db.String(5), nullable=True)  # "HH:mm", free-form per frontend contract
    closing_time = db.Column(db.String(5), nullable=True)
    employee_range = db.Column(db.Enum(EmployeeRange, name="business_profile_employee_range", schema="business"), nullable=True)

    # --- Section 5: Operating History ---
    years_operating = db.Column(db.Enum(OperatingHistory, name="business_profile_operating_history", schema="business"), nullable=True)

    # --- Section 6: Supplier Info ---
    supplier_sources = db.Column(ARRAY(db.String), nullable=False, default=list)

    # --- Section 7: Verification (read-only from this domain's API --
    # see services/business_profile_service.py's get_profile for where
    # phone_verified/email_verified actually come from. The other four
    # have no backing verification system yet; they stay False until
    # one exists, never silently faked True.) ---
    business_info_complete = db.Column(db.Boolean, nullable=False, default=False)
    location_complete = db.Column(db.Boolean, nullable=False, default=False)
    identity_verified = db.Column(db.Boolean, nullable=False, default=False)
    documents_verified = db.Column(db.Boolean, nullable=False, default=False)
