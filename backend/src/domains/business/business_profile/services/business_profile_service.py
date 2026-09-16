"""
Business Profile business logic.

TWO THINGS THIS SERVICE DOES THAT THE REPOSITORY/MODEL ALONE CANNOT:

1. "Same as my account" is resolved LIVE, not from a stale stored
   copy. When uses_same_as_account_phone/Email is True, the row's own
   phone/email columns are NOT what gets returned -- the actual
   User.phone_number/email is read fresh every time. This matters
   because if someone changes their account phone number later, their
   business contact info that's marked "same as account" must follow
   automatically, not silently drift from what the account really is.
   The row still stores its own phone/email for the "different number"
   case (uses_same_as_account_phone=False) -- see
   models/business_profile.py's ContactDetails-equivalent columns.

2. THE "verification" BLOCK IS GONE, and this is the note that used to
   defend it. It returned four booleans, and not one of them could
   tell a reader anything (V2_18 Part 2):

     phoneVerified          could only ever be TRUE. Every route on
                            this blueprint is @fully_authenticated,
                            which already means the OTP flow completed
                            -- so nobody who can see the answer can see
                            it be False.
     emailVerified          could only ever be FALSE. This backend has
                            no email-verification flow, and reusing the
                            phone signal for it would have
                            misrepresented what was actually checked.
     businessInfoComplete   never written by anything, ever.
     locationComplete       never written by anything, ever.

   Rendered as a checklist, that is four boxes of which two can never
   tick and one can never fail to -- which implied a review of an
   informal business that does not happen and that we have decided
   should not. identity_verified and documents_verified were removed
   from the model earlier for the same reason; this is the rest of that
   removal.

   COMPLETENESS SURVIVES, because it is a real question the demand
   engine acts on. It is answered by the frontend's own
   completionCalculator from the data itself, which is both more
   accurate than the two columns and impossible to leave stale.
"""
from __future__ import annotations

import uuid
from typing import Any

from src.domains.auth.models.user import User
from src.domains.business.business_profile.models.business_profile import BusinessProfile
from src.domains.business.business_profile.repositories.business_profile_repository import (
    BusinessProfileRepository,
)
from src.extensions import db


def _refresh_normalized_contact(profile: BusinessProfile, user: User) -> None:
    """Keeps normalized_phone/normalized_email in sync with the
    EFFECTIVE contact value (respecting uses_same_as_account_phone/
    Email, same live-resolution rule get_profile's own _to_dict
    already applies) -- added for Find Business (network/connections'
    own supplier-side mirror of Find Supplier).

    KNOWN LIMITATION, honestly flagged rather than silently assumed
    fine: this only runs when the BUSINESS PROFILE itself is touched
    (update_contact_details below, and the initial seed at
    verification). If a business is using "same as account" and later
    changes their ACCOUNT phone/email through some other path, this
    column won't refresh until the business profile is touched again
    -- there is currently no real account-phone/email-change endpoint
    at all (My Account's own contact editing is still mock-backed), so
    this gap can't actually manifest yet. Worth revisiting the moment
    a real account-contact-change endpoint exists.
    """
    from src.shared.validation.identifiers import normalize_email, normalize_phone

    effective_phone = user.phone_number if profile.uses_same_as_account_phone else profile.phone
    effective_email = user.email if profile.uses_same_as_account_email else profile.email

    profile.normalized_phone = normalize_phone(effective_phone) if effective_phone else None
    profile.normalized_email = normalize_email(effective_email) if effective_email else None


class BusinessProfileService:
    @staticmethod
    def get_profile(business_id: uuid.UUID) -> dict:
        profile = BusinessProfileRepository.get_or_create_for_business(business_id)
        user = User.query.get(business_id)
        return BusinessProfileService._to_dict(profile, user)

    @staticmethod
    def update_business_details(business_id: uuid.UUID, data: dict[str, Any]) -> dict:
        profile = BusinessProfileRepository.get_or_create_for_business(business_id)
        if "businessName" in data:
            name = (data["businessName"] or "").strip()
            if not name:
                from src.domains.business.business_profile.services.errors import BusinessProfileValidationError
                raise BusinessProfileValidationError("Give your business a name.", field="businessName")
            profile.business_name = name
        if "category" in data:
            profile.category = data["category"]
        if "businessType" in data:
            profile.business_type = data["businessType"]
        if "description" in data:
            profile.description = data["description"]
        if "operatingModel" in data:
            profile.operating_model = data["operatingModel"]
        db.session.commit()
        return BusinessProfileService.get_profile(business_id)

    @staticmethod
    def update_contact_details(business_id: uuid.UUID, data: dict[str, Any]) -> dict:
        profile = BusinessProfileRepository.get_or_create_for_business(business_id)
        for field, column in [
            ("phone", "phone"), ("usesSameAsAccountPhone", "uses_same_as_account_phone"),
            ("email", "email"), ("usesSameAsAccountEmail", "uses_same_as_account_email"),
            ("whatsapp", "whatsapp"), ("whatsappSameAsPhone", "whatsapp_same_as_phone"),
            ("whatsappNotUsed", "whatsapp_not_used"),
            ("facebook", "facebook"), ("instagram", "instagram"),
        ]:
            if field in data:
                setattr(profile, column, data[field])
        user = User.query.get(business_id)
        if user:
            _refresh_normalized_contact(profile, user)
        db.session.commit()
        return BusinessProfileService.get_profile(business_id)

    @staticmethod
    def update_location(business_id: uuid.UUID, data: dict[str, Any]) -> dict:
        profile = BusinessProfileRepository.get_or_create_for_business(business_id)
        for field, column in [
            ("province", "province"), ("cityOrTown", "city_or_town"),
            ("physicalAddress", "physical_address"),
            ("latitude", "latitude"), ("longitude", "longitude"),
        ]:
            if field in data:
                setattr(profile, column, data[field])
        db.session.commit()
        return BusinessProfileService.get_profile(business_id)

    @staticmethod
    def update_trading_details(business_id: uuid.UUID, data: dict[str, Any]) -> dict:
        profile = BusinessProfileRepository.get_or_create_for_business(business_id)
        for field, column in [
            ("buysCategories", "buys_categories"), ("customerTypes", "customer_types"),
            ("restockRhythm", "restock_rhythm"), ("weeklySpendBand", "weekly_spend_band"),
            ("stockCollection", "stock_collection"),
            ("operatingDays", "operating_days"),
            ("openingTime", "opening_time"), ("closingTime", "closing_time"),
            ("employeeRange", "employee_range"),
        ]:
            if field in data:
                setattr(profile, column, data[field])
        db.session.commit()
        return BusinessProfileService.get_profile(business_id)

    @staticmethod
    def update_operating_history(business_id: uuid.UUID, data: dict[str, Any]) -> dict:
        profile = BusinessProfileRepository.get_or_create_for_business(business_id)
        if "yearsOperating" in data:
            profile.years_operating = data["yearsOperating"]
        db.session.commit()
        return BusinessProfileService.get_profile(business_id)

    @staticmethod
    def update_supplier_info(business_id: uuid.UUID, data: dict[str, Any]) -> dict:
        profile = BusinessProfileRepository.get_or_create_for_business(business_id)
        if "sources" in data:
            profile.supplier_sources = data["sources"]
        db.session.commit()
        return BusinessProfileService.get_profile(business_id)

    # -----------------------------------------------------------------

    @staticmethod
    def _to_dict(profile: BusinessProfile, user: "User | None") -> dict:
        live_phone = user.phone_number if user else None
        live_email = user.email if user else None

        return {
            "id": str(profile.id),
            "businessDetails": {
                "businessName": profile.business_name,
                "category": profile.category.value if profile.category else None,
                "businessType": profile.business_type.value if profile.business_type else None,
                "description": profile.description,
                "operatingModel": profile.operating_model.value if profile.operating_model else None,
            },
            "contactDetails": {
                "phone": live_phone if profile.uses_same_as_account_phone else profile.phone,
                "usesSameAsAccountPhone": profile.uses_same_as_account_phone,
                "email": live_email if profile.uses_same_as_account_email else profile.email,
                "usesSameAsAccountEmail": profile.uses_same_as_account_email,
                "whatsapp": profile.whatsapp,
                "whatsappSameAsPhone": profile.whatsapp_same_as_phone,
                "whatsappNotUsed": profile.whatsapp_not_used,
                "facebook": profile.facebook,
                "instagram": profile.instagram,
            },
            "location": {
                "province": profile.province.value if profile.province else None,
                "cityOrTown": profile.city_or_town,
                "physicalAddress": profile.physical_address,
                # float(), NOT THE RAW COLUMN. These are NUMERIC(9,6)
                # now, matching the supplier's collection_* pair, and a
                # Decimal serialises as a STRING -- "-26.204100" where
                # the app's BusinessLocation says number. Every supplier-
                # side serialiser of these columns already wraps them
                # (supplier_profile_routes, discovery_service,
                # cart_service); this is the fourth and the reason the
                # type change was safe.
                "latitude": float(profile.latitude) if profile.latitude is not None else None,
                "longitude": float(profile.longitude) if profile.longitude is not None else None,
            },
            "tradingDetails": {
                "buysCategories": profile.buys_categories or [],
                "customerTypes": profile.customer_types or [],
                "restockRhythm": profile.restock_rhythm.value if profile.restock_rhythm else None,
                "weeklySpendBand": (
                    profile.weekly_spend_band.value if profile.weekly_spend_band else None
                ),
                # PASSED THROUGH RAW, INCLUDING None. A `or "DELIVERY"`
                # here would be the exact mistake the column exists to
                # avoid: it would turn "never asked" into an answer on
                # the way out of the database.
                "stockCollection": (
                    profile.stock_collection.value if profile.stock_collection else None
                ),
                "operatingDays": profile.operating_days or [],
                "openingTime": profile.opening_time,
                "closingTime": profile.closing_time,
                "employeeRange": profile.employee_range.value if profile.employee_range else None,
            },
            "operatingHistory": {
                "yearsOperating": profile.years_operating.value if profile.years_operating else None,
            },
            "supplierInfo": {
                "sources": profile.supplier_sources or [],
            },
            "createdAt": profile.created_at.isoformat(),
            "updatedAt": profile.updated_at.isoformat(),
        }
