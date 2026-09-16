"""
Business Profile validation schemas -- one per section, matching the
frontend's per-section save calls exactly (useBusinessProfileMutations
has one mutation per section; this backend has one PATCH route and one
schema per section to match).

Every enum/option field is validated with OneOf against the SAME string
values the frontend's types.ts declares (e.g. "FOOD_BEVERAGES", "HOME"),
not re-derived or guessed -- copy-checked against that file directly.
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate

from src.domains.business.business_profile.models.business_profile import (
    RestockRhythm,
    WeeklySpendBand,
)
from src.domains.catalogue.products.models.taxonomy import ProductCategory

_CATEGORY_OPTIONS = ["FOOD_BEVERAGES", "CLOTHING_FASHION", "BEAUTY_COSMETICS", "ELECTRONICS", "RETAIL", "PROFESSIONAL_SERVICES", "HOME_HOUSEHOLD", "OTHER"]
_BUSINESS_TYPE_OPTIONS = ["SOLE_TRADER", "PARTNERSHIP", "FAMILY_BUSINESS", "REGISTERED_COMPANY", "OTHER"]
_OPERATING_MODEL_OPTIONS = ["HOME", "SHOP", "MARKET_STALL", "STREET_MOBILE", "ONLINE", "MULTIPLE_LOCATIONS", "OTHER"]
_PROVINCE_OPTIONS = ["EASTERN_CAPE", "FREE_STATE", "GAUTENG", "KWAZULU_NATAL", "LIMPOPO", "MPUMALANGA", "NORTHERN_CAPE", "NORTH_WEST", "WESTERN_CAPE"]
_CUSTOMER_TYPE_OPTIONS = ["INDIVIDUALS", "OTHER_BUSINESSES", "FRIENDS_COMMUNITY", "ORGANISATIONS", "OTHER"]

# DERIVED FROM THE ENUMS, NOT RETYPED. Every other option list in this
# file is a hand-written copy that has to be remembered when the enum
# changes -- BEAUTY_HAIR was added to ProductCategory on 2026-09-13 and
# a hardcoded list here would already be wrong.
_PRODUCT_CATEGORY_OPTIONS = [c.value for c in ProductCategory]
_RESTOCK_RHYTHM_OPTIONS = [r.value for r in RestockRhythm]
_WEEKLY_SPEND_BAND_OPTIONS = [b.value for b in WeeklySpendBand]
_ORDER_CHANNEL_OPTIONS = ["IN_PERSON", "WHATSAPP", "PHONE", "SOCIAL_MEDIA", "ONLINE", "OTHER"]
_PAYMENT_METHOD_OPTIONS = ["CASH", "EFT", "CARD", "MOBILE_PAYMENT", "OTHER"]
_WEEKDAY_OPTIONS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
_EMPLOYEE_RANGE_OPTIONS = ["JUST_ME", "TWO_TO_FIVE", "SIX_TO_TEN", "ELEVEN_TO_TWENTY", "MORE_THAN_TWENTY"]
_OPERATING_HISTORY_OPTIONS = ["LESS_THAN_6_MONTHS", "SIX_MONTHS_TO_1_YEAR", "ONE_TO_2_YEARS", "TWO_TO_5_YEARS", "FIVE_PLUS_YEARS"]
_SUPPLIER_SOURCE_OPTIONS = ["LOCAL_SUPPLIERS", "WHOLESALERS", "DISTRIBUTORS", "MANUFACTURERS", "MARKETS", "OTHER_BUSINESSES", "OTHER"]


class UpdateBusinessDetailsSchema(Schema):
    businessName = fields.String(required=False, validate=validate.Length(min=1, max=200))
    category = fields.String(required=False, allow_none=True, validate=validate.OneOf(_CATEGORY_OPTIONS))
    businessType = fields.String(required=False, allow_none=True, validate=validate.OneOf(_BUSINESS_TYPE_OPTIONS))
    description = fields.String(required=False, allow_none=True, validate=validate.Length(max=250))
    operatingModel = fields.String(required=False, allow_none=True, validate=validate.OneOf(_OPERATING_MODEL_OPTIONS))


class UpdateContactDetailsSchema(Schema):
    phone = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    usesSameAsAccountPhone = fields.Boolean(required=False)
    email = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    usesSameAsAccountEmail = fields.Boolean(required=False)
    whatsapp = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    whatsappSameAsPhone = fields.Boolean(required=False)
    whatsappNotUsed = fields.Boolean(required=False)
    facebook = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    instagram = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))


class UpdateLocationSchema(Schema):
    province = fields.String(required=False, allow_none=True, validate=validate.OneOf(_PROVINCE_OPTIONS))
    cityOrTown = fields.String(required=False, allow_none=True, validate=validate.Length(max=120))
    physicalAddress = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
    latitude = fields.Float(required=False, allow_none=True)
    longitude = fields.Float(required=False, allow_none=True)


class UpdateTradingDetailsSchema(Schema):
    # VALIDATED AGAINST THE REAL TAXONOMY, not a free string. A declared
    # category that is not a ProductCategory cannot be matched to
    # anything, so accepting one would store a need the engine can never
    # serve and never explain.
    buysCategories = fields.List(
        fields.String(validate=validate.OneOf(_PRODUCT_CATEGORY_OPTIONS)), required=False
    )
    customerTypes = fields.List(fields.String(validate=validate.OneOf(_CUSTOMER_TYPE_OPTIONS)), required=False)
    restockRhythm = fields.String(
        required=False, allow_none=True, validate=validate.OneOf(_RESTOCK_RHYTHM_OPTIONS)
    )
    weeklySpendBand = fields.String(
        required=False, allow_none=True, validate=validate.OneOf(_WEEKLY_SPEND_BAND_OPTIONS)
    )
    # TRI-STATE, SO allow_none MATTERS. None is a real answer here --
    # "not asked yet" -- and must round-trip rather than collapse into
    # False. See the column's own comment.
    canCollect = fields.Boolean(required=False, allow_none=True)
    operatingDays = fields.List(fields.String(validate=validate.OneOf(_WEEKDAY_OPTIONS)), required=False)
    openingTime = fields.String(required=False, allow_none=True, validate=validate.Length(max=5))
    closingTime = fields.String(required=False, allow_none=True, validate=validate.Length(max=5))
    employeeRange = fields.String(required=False, allow_none=True, validate=validate.OneOf(_EMPLOYEE_RANGE_OPTIONS))


class UpdateOperatingHistorySchema(Schema):
    yearsOperating = fields.String(required=False, allow_none=True, validate=validate.OneOf(_OPERATING_HISTORY_OPTIONS))


class UpdateSupplierInfoSchema(Schema):
    sources = fields.List(fields.String(validate=validate.OneOf(_SUPPLIER_SOURCE_OPTIONS)), required=False)
