"""
SupplierProfile -- a supplier's own core identity record: the business
name, category, general location, and verification-adjacent fields a
Business needs to recognise a real-world supplier during search
(file.txt/FILE2.txt Phase 1). Lives HERE, in domains/supplier/
supplier_profile/, not inside network/connections -- this
domain was already reserved (empty scaffolding) for exactly this
purpose, and FILE2.txt explicitly warns against "duplicate Supplier
models". network/connections's service queries this model via
SupplierProfileRepository; it does not own a copy of this data.

ONE-TO-ONE WITH User: supplier_id is unique, not just indexed -- a
supplier's identity lives on auth.users (the root identity, per
user.py's own docstring: "Business/Supplier profile data... belongs on
future BusinessProfile / SupplierProfile models, connected to this
User by a relationship"); this table is exactly that promised
relationship being fulfilled for the Supplier side, mirroring how
BusinessProfile already does it for Business -- verified directly
against business_profile.py: its own FK column is named `business_id`
(not `user_id`), so this column is named `supplier_id` to match that
exact domain-role-prefixed convention, not a generic name.

SEARCH FIELDS ARE NORMALIZED, NEVER DISPLAY FIELDS: normalized_phone /
normalized_email exist purely for indexed exact-match search (see
repositories/supplier_profile_repository.py) -- display always reads
from the User row's own phone_number/email (or, for masking, goes
through shared.helpers.mask_email / a phone equivalent), never from
these columns directly, so this table never becomes a second source of
truth for a supplier's actual contact details.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class SupplierVerificationStatus(str, enum.Enum):
    """Deliberately separate from auth.users.verification_status
    (account-level, real, generic across Business/Supplier) -- this is
    the SUPPLIER-specific commercial trust indicator file.txt's own
    verification-wall phase describes ("stronger commercial
    verification" for suppliers specifically). Two different concepts
    that happen to share similar-looking states; keeping them as
    separate columns/enums avoids one overloading the other's meaning
    later when the verification wall (file.txt Phase 21+) is built."""

    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class PhotoVisibility(str, enum.Enum):
    """WHO can see the resolved photo (see visible_image_source below
    for WHICH photo). Default is CONNECTIONS, not EVERYONE -- agreed
    during architecture review: showing a photo in bare search
    results (before any relationship exists) is a different, more
    exposed choice than showing it to someone you're already
    connected with, and the cautious default should require an
    explicit opt-in to go wider, not a silent one."""

    EVERYONE = "everyone"
    CONNECTIONS = "connections"
    NOBODY = "nobody"


class VisibleImageSource(str, enum.Enum):
    """WHICH photo gets shown, once photo_visibility already allows
    showing one at all. PERSONAL reads live from auth.users.
    profile_image_url (see that column's own docstring on why it's
    never copied here); BUSINESS reads business_image_url on this
    same row. NONE is the default -- nothing shows until the person
    actively picks one, even if photo_visibility would otherwise
    allow it."""

    PERSONAL = "personal"
    BUSINESS = "business"
    NONE = "none"


class SupplierProfile(BaseModel):
    __tablename__ = "supplier_profiles"
    __table_args__ = (
        db.UniqueConstraint("supplier_id", name="uq_supplier_profiles_supplier_id"),
        # Both search paths need their own index -- phone and email
        # are looked up independently, never together, so a single
        # composite index wouldn't serve either query well.
        db.Index("ix_supplier_profiles_normalized_phone", "normalized_phone"),
        db.Index("ix_supplier_profiles_normalized_email", "normalized_email"),
        db.Index("ix_supplier_profiles_business_name", "business_name"),
        {"schema": "supplier"},
    )

    supplier_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)

    business_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(120), nullable=True)
    # General only (suburb/city) -- file.txt §4's privacy framing
    # applies to what's STORED for search purposes here too, not just
    # what's returned: this column was never designed to hold a full
    # street address.
    location = db.Column(db.String(120), nullable=True)
    description = db.Column(db.String(500), nullable=True)

    verification_status = db.Column(
        db.Enum(SupplierVerificationStatus, name="supplier_verification_status", schema="supplier"),
        nullable=False,
        default=SupplierVerificationStatus.UNVERIFIED,
    )

    # Normalized, indexed, search-only -- see module docstring.
    normalized_phone = db.Column(db.String(20), nullable=True)
    normalized_email = db.Column(db.String(255), nullable=True)

    # A business-specific image, distinct from the PERSONAL photo on
    # auth.users -- a supplier can be shown as themselves or as their
    # business, their choice (visible_image_source below).
    business_image_url = db.Column(db.String(500), nullable=True)
    visible_image_source = db.Column(
        db.Enum(VisibleImageSource, name="visible_image_source", schema="supplier"),
        nullable=False,
        default=VisibleImageSource.NONE,
    )
    photo_visibility = db.Column(
        db.Enum(PhotoVisibility, name="photo_visibility", schema="supplier"),
        nullable=False,
        default=PhotoVisibility.CONNECTIONS,
    )

    def to_search_result_dict(self, matched_field: str, masked_identifier: str) -> dict:
        """The PRIVACY-NARROWED shape for a search result row -- see
        file.txt §4: enough to recognise the supplier, never the full
        stored record. Deliberately does NOT reuse to_public_dict-style
        full serialization; this method exists specifically so nobody
        accidentally widens a search response by generalizing it later."""
        return {
            "id": str(self.id),
            "businessName": self.business_name,
            "category": self.category,
            "location": self.location,
            "verificationStatus": self.verification_status.value if self.verification_status else None,
            "matchedField": matched_field,
            "maskedMatchedIdentifier": masked_identifier,
        }

    def to_profile_preview_dict(self, connection_status: str, visible_photo_url: str | None = None) -> dict:
        """One level deeper than a search result (file.txt §4's
        "supplier profile" step) -- still narrow, still not the
        supplier's full record. connection_status AND
        visible_photo_url are both passed in rather than resolved
        here, since both depend on data this model doesn't own
        (ConnectionRequest, and auth.users.profile_image_url) --
        same reasoning connection_status's own docstring already
        established, extended to the photo. Deliberately NOT added to
        to_search_result_dict above -- a photo is a step further than
        bare search results should expose, even under EVERYONE
        visibility; the profile preview is where richer identity
        information belongs."""
        return {
            "id": str(self.id),
            "businessName": self.business_name,
            "category": self.category,
            "location": self.location,
            "verificationStatus": self.verification_status.value if self.verification_status else None,
            "memberSinceYear": self.created_at.year if self.created_at else None,
            "description": self.description,
            "connectionStatus": connection_status,
            "photoUrl": visible_photo_url,
        }
