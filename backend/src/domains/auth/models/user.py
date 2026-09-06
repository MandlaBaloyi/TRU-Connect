"""
User Model -- the root authentication entity for TRU Connect.



DESIGN
------
A User represents AUTHENTICATION ONLY. Business/Supplier profile data
(business name, category, trading info, SA ID number, etc.) is
deliberately NOT stored here -- it belongs on future BusinessProfile /
SupplierProfile models, connected to this User by a relationship once
those tables exist . This is a hard rule 
, not an oversight: keeping authentication identity separate from
business-profile data means a single login identity can, in future,
support more than one "hat" (e.g. an admin/financial-partner role --
 without
requiring a redesign of this table.

WHY IT EXISTS
-------------
Every other domain in this backend (Business, Supplier, Trust, Verification
ultimately traces back to a User for "who is
allowed to do this." Nothing else can be built correctly until this
identity root exists.

INTEGRATION WITH PREVIOUS FILES
--------------------------------
Inherits id / created_at / updated_at / is_deleted / deleted_at from
BaseModel (src/core/base_model.py,) -- this is exactly what that
mixin was built for. No other  file needs to change for this
model to exist; src/models/__init__.py just needs to import it so
Flask-Migrate's autogenerate can see it (handled by this script's
integration step, not by editing base_model.py itself).
"""
from __future__ import annotations

import enum
from typing import Optional

from src.core.base_model import BaseModel
from src.extensions import db


class UserRole(str, enum.Enum):
    """String enum so values serialize cleanly to JSON as "business" /
    "supplier", not an integer or a Python repr."""

    BUSINESS = "business"
    SUPPLIER = "supplier"
    # Reserved for a future admin/financial-partner role
    # --
    # not used by any current registration path.
    ADMIN = "admin"


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class User(BaseModel):
    """Root authentication entity. UUID primary key and timezone-aware
    created_at/updated_at/soft-delete columns come from BaseModel."""

    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}  # <-- Links table to the auth domain schema

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum(UserRole, name="user_role", schema="auth"),  
        nullable=False
    )

    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    # Captured at SUPPLIER registration, where it's mandatory (the owner
    # name is the optional one) -- carried here rather than seeded
    # straight onto SupplierProfile because that row is deliberately not
    # created until email verification (supplier_profile_repository.py's
    # docstring on the FK-no-cascade / hard-delete hazard). Same
    # lifecycle as first_name/last_name: staged on the users row,
    # consumed by otp_service._seed_supplier_profile at verification,
    # hard-deleted cleanly with the user if they never verify. Validated
    # to shared.validation.business_name's 50-char limit at the API
    # boundary; 120 here is headroom, matching sibling columns. Nullable
    # so business-role rows (which don't collect it) and pre-existing
    # rows are valid.
    business_name = db.Column(db.String(120), nullable=True)
    phone_number = db.Column(db.String(32), nullable=True)
    # The ONE personal photo, shared across roles -- a person only has
    # one face regardless of whether they're viewed as a business or
    # supplier. Read LIVE at request time by whichever profile chose
    # PERSONAL as its visible_image_source (see SupplierProfile/
    # BusinessProfile's own photo_visibility/visible_image_source
    # columns), never copied onto those tables -- same "read fresh,
    # never a stale duplicate" rule BusinessProfile's own
    # uses_same_as_account_phone/email already established.
    profile_image_url = db.Column(db.String(500), nullable=True)

    account_status = db.Column(
        db.Enum(AccountStatus, name="account_status", schema="auth"),  
        nullable=False,
        default=AccountStatus.ACTIVE,
    )
    verification_status = db.Column(
        db.Enum(VerificationStatus, name="verification_status", schema="auth"),  
        nullable=False,
        default=VerificationStatus.UNVERIFIED,
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<User {self.email} ({self.role.value if self.role else '?'})>"

    def to_public_dict(self) -> dict:
        """Explicit allow-list of fields safe to return to a client.

        NEVER include password_hash here, and never add a field to this
        method without checking docs/05_BACKEND_API_SPECIFICATION.txt
        first -- "Never expose sensitive fields" is a hard rule, not a
        style preference.
        """
        return {
            "id": str(self.id),
            "email": self.email,
            "role": self.role.value if self.role else None,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number,
            "profile_image_url": self.profile_image_url,
            "account_status": self.account_status.value if self.account_status else None,
            "verification_status": self.verification_status.value if self.verification_status else None,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }