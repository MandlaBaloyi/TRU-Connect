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


class RestockRhythm(str, enum.Enum):
    """HOW OFTEN THIS SHOP RESTOCKS -- one tap, and the single most
    valuable thing the demand engine can know on day one.

    Without it the engine waits for months of order history before it
    can time anything, and a shop that restocks daily is served exactly
    as badly as one that restocks monthly in the meantime.

    IRREGULAR IS A REAL ANSWER, not a refusal. Plenty of shops buy when
    they run out and when they have cash, and recording that honestly
    is better than forcing a cadence the engine will then be wrong
    about.
    """

    DAILY = "DAILY"
    TWICE_WEEKLY = "TWICE_WEEKLY"
    WEEKLY = "WEEKLY"
    FORTNIGHTLY = "FORTNIGHTLY"
    MONTHLY = "MONTHLY"
    IRREGULAR = "IRREGULAR"


class WeeklySpendBand(str, enum.Enum):
    """ROUGHLY WHAT THEY SPEND ON STOCK IN A WEEK.

    A BAND, NEVER A NUMBER. An exact figure is a question people
    hesitate over, get wrong, and feel examined by -- and the engine
    does not need precision. It needs to stop showing a R5,000 pallet
    to a shop that buys R800 a week, which a band answers completely.

    NOT A FINANCIAL ASSESSMENT AND MUST NEVER BE PRESENTED AS ONE. It
    sizes a basket. V2_03 is explicit that self-reported figures cannot
    support lending, and this is self-reported.
    """

    UNDER_500 = "UNDER_500"
    R500_TO_2000 = "R500_TO_2000"
    R2000_TO_5000 = "R2000_TO_5000"
    R5000_TO_10000 = "R5000_TO_10000"
    OVER_10000 = "OVER_10000"


class OperatingHistory(str, enum.Enum):
    LESS_THAN_6_MONTHS = "LESS_THAN_6_MONTHS"
    SIX_MONTHS_TO_1_YEAR = "SIX_MONTHS_TO_1_YEAR"
    ONE_TO_2_YEARS = "ONE_TO_2_YEARS"
    TWO_TO_5_YEARS = "TWO_TO_5_YEARS"
    FIVE_PLUS_YEARS = "FIVE_PLUS_YEARS"


class PhotoVisibility(str, enum.Enum):
    """Mirrors supplier.photo_visibility exactly, member-for-member,
    so both roles serialize the same API shape ("everyone"/
    "connections"/"nobody") -- see that file's own docstring for the
    full reasoning (CONNECTIONS default, not EVERYONE)."""

    EVERYONE = "everyone"
    CONNECTIONS = "connections"
    NOBODY = "nobody"


class VisibleImageSource(str, enum.Enum):
    """Mirrors supplier.visible_image_source exactly -- PERSONAL reads
    live from auth.users.profile_image_url, BUSINESS reads
    business_image_url on this same row, NONE (the default) shows
    nothing until the person actively picks one."""

    PERSONAL = "personal"
    BUSINESS = "business"
    NONE = "none"


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
        # Added for Find Business (the supplier-side mirror of Find
        # Supplier's own search) -- both search paths need their own
        # index, same reasoning as ix_supplier_profiles_normalized_phone/
        # email: phone and email are looked up independently, never
        # together.
        db.Index("ix_business_profiles_normalized_phone", "normalized_phone"),
        db.Index("ix_business_profiles_normalized_email", "normalized_email"),
        db.Index("ix_business_profiles_business_name", "business_name"),
        {"schema": "business"},
    )

    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)

    # --- Search fields (Find Business) -----------------------------------
    # NORMALIZED, INDEXED, SEARCH-ONLY -- mirrors supplier_profiles'
    # own normalized_phone/normalized_email exactly (see
    # supplier_profile.py's own module docstring for the full
    # reasoning). Reflects the EFFECTIVE phone/email at the moment the
    # profile was last touched (respecting uses_same_as_account_phone/
    # Email below) -- see business_profile_service.py's own
    # _refresh_normalized_contact for where these actually get kept in
    # sync, and its own docstring for the one known limitation.
    normalized_phone = db.Column(db.String(20), nullable=True)
    normalized_email = db.Column(db.String(255), nullable=True)

    # Mirrors SupplierProfile's own three columns exactly -- see that
    # model's own docstring on the full reasoning.
    business_image_url = db.Column(db.String(500), nullable=True)
    visible_image_source = db.Column(
        db.Enum(VisibleImageSource, name="visible_image_source", schema="business"),
        nullable=False,
        default=VisibleImageSource.NONE,
    )
    photo_visibility = db.Column(
        db.Enum(PhotoVisibility, name="photo_visibility", schema="business"),
        nullable=False,
        default=PhotoVisibility.CONNECTIONS,
    )

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
    # NUMERIC(9,6), MATCHING SupplierProfile.collection_latitude/longitude.
    # These two are compared against each other on every "collect near
    # you" calculation, which is the worst place for the pair to round
    # differently. Six decimals is about 11cm -- a fixed, stateable
    # precision, where a float's precision depends on the value.
    latitude = db.Column(db.Numeric(9, 6), nullable=True)
    longitude = db.Column(db.Numeric(9, 6), nullable=True)

    # --- Section 4: Trading Details ---
    # WHAT THEY BUY, AGAINST THE REAL TAXONOMY. Replaces `products`,
    # which asked what they SELL from a per-category list of adjectives
    # -- and which, for five of the eight business categories including
    # RETAIL, offered a shopkeeper the answer "Products". That is not a
    # weak signal, it is no signal, and it was the strongest thing the
    # demand engine was supposed to read.
    #
    # SELL BECAME BUY DELIBERATELY. A salon SELLS haircuts and BUYS
    # relaxers; only the second is orderable here, and only the second
    # tells the feed anything.
    #
    # Holds ProductCategory values (catalogue/products/taxonomy.py), so
    # a declared need lands directly on the taxonomy the catalogue and
    # the chips already use -- no mapping table to drift.
    buys_categories = db.Column(ARRAY(db.String), nullable=False, default=list)
    customer_types = db.Column(ARRAY(db.String), nullable=False, default=list)
    # HOW OFTEN AND HOW MUCH -- the two questions that let the engine be
    # useful before a single order exists. See the enums above.
    restock_rhythm = db.Column(
        db.Enum(RestockRhythm, name="business_profile_restock_rhythm", schema="business"),
        nullable=True,
    )
    weekly_spend_band = db.Column(
        db.Enum(WeeklySpendBand, name="business_profile_weekly_spend_band", schema="business"),
        nullable=True,
    )
    operating_days = db.Column(ARRAY(db.String), nullable=False, default=list)
    opening_time = db.Column(db.String(5), nullable=True)  # "HH:mm", free-form per frontend contract
    closing_time = db.Column(db.String(5), nullable=True)
    employee_range = db.Column(db.Enum(EmployeeRange, name="business_profile_employee_range", schema="business"), nullable=True)

    # --- Section 5: Operating History ---
    years_operating = db.Column(db.Enum(OperatingHistory, name="business_profile_operating_history", schema="business"), nullable=True)

    # --- Section 6: Supplier Info ---
    supplier_sources = db.Column(ARRAY(db.String), nullable=False, default=list)

    # --- Section 7: Completeness ---
    # identity_verified and documents_verified WERE HERE AND ARE GONE.
    # They were the SUPPLIER model's concepts sitting on the business
    # table: the verification curtain gates who may SELL, and an
    # informal business is not checked in order to shop. They never had
    # a backing system, stayed False for every row that ever existed,
    # and their only real effect was to imply a review that does not
    # happen and should not.
    #
    # What remains is completeness, which is about how much this shop
    # has told us -- and that is a question the demand engine genuinely
    # acts on, not a judgement about them.
    business_info_complete = db.Column(db.Boolean, nullable=False, default=False)
    location_complete = db.Column(db.Boolean, nullable=False, default=False)

    # --- Find Business narrowing methods -----------------------------
    # Mirror SupplierProfile.to_search_result_dict/to_profile_preview_dict
    # exactly -- same file.txt §4 privacy narrowing, same reasoning: a
    # supplier searching for a business sees enough to recognise "yes,
    # that's my customer", never the business's full stored trading/
    # operating/verification record.

    def to_search_result_dict(self) -> dict:
        """No longer takes matched_field/masked_identifier -- see
        SupplierProfile.to_search_result_dict's own docstring
        (supplier_profile.py) for the full reasoning; this mirrors
        that simplification exactly."""
        return {
            "id": str(self.id),
            "businessName": self.business_name,
            "category": self.category.value if self.category else None,
            "location": self.city_or_town,
        }

    def to_profile_preview_dict(self, connection_status: str, visible_photo_url: str | None = None) -> dict:
        """visible_photo_url is passed in, not resolved here -- same
        reasoning as SupplierProfile's own to_profile_preview_dict:
        the actual resolution needs auth.users.profile_image_url and
        an ACTIVE-connection check, neither of which this model owns."""
        return {
            "id": str(self.id),
            "businessName": self.business_name,
            "category": self.category.value if self.category else None,
            "location": self.city_or_town,
            "memberSinceYear": self.created_at.year if self.created_at else None,
            "description": self.description,
            "connectionStatus": connection_status,
            "photoUrl": visible_photo_url,
        }
