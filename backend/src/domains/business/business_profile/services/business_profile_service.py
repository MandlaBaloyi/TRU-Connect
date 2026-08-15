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

2. Verification status is derived from REAL signals where they exist,
   never faked. phone_verified reflects User.verification_status
   (VERIFIED means the OTP flow completed -- see
   domains/auth/models/user.py) -- that's a genuine, existing signal.
   email_verified is honestly False: this backend has no distinct
   email-verification flow (only phone OTP) -- reusing the phone
   signal for email would misrepresent what was actually verified, so
   it stays False until a real email-verification mechanism exists.
   business_info_complete/location_complete/identity_verified/
   documents_verified have no backing system at all yet and stay
   False -- Business Profile only ever DISPLAYS verification state, it
   never invents it (see types.ts's VerificationStatus docstring on
   the frontend side of this same rule).
"""
from __future__ import annotations

import uuid
from typing import Any

from src.domains.auth.models.user import User, VerificationStatus as UserVerificationStatus
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
            ("products", "products"), ("customerTypes", "customer_types"),
            ("orderChannels", "order_channels"), ("paymentMethods", "payment_methods"),
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
        phone_verified = bool(user and user.verification_status == UserVerificationStatus.VERIFIED)

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
                "latitude": profile.latitude,
                "longitude": profile.longitude,
            },
            "tradingDetails": {
                "products": profile.products or [],
                "customerTypes": profile.customer_types or [],
                "orderChannels": profile.order_channels or [],
                "paymentMethods": profile.payment_methods or [],
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
            "verification": {
                "phoneVerified": phone_verified,
                "emailVerified": False,
                "businessInfoComplete": profile.business_info_complete,
                "locationComplete": profile.location_complete,
                "identityVerified": profile.identity_verified,
                "documentsVerified": profile.documents_verified,
            },
            "createdAt": profile.created_at.isoformat(),
            "updatedAt": profile.updated_at.isoformat(),
        }
