"""
SupplierProfileImage -- a supplier's own profile photo and cover
banner, as real Cloudinary-backed uploads. Real FK to
supplier_profiles.id, not a polymorphic owner column -- exactly the
pattern shared/media/mixins.py's own docstring anticipated ("profile
photos, verification documents ... later" each build their OWN table
using MediaAssetMixin plus their own real foreign key).

Direct counterpart to products/models/product_media.py -- same mixin,
same PENDING -> APPROVED/REJECTED scan lifecycle, same "treat an
upload as untrusted until scanning completes" rule. The one structural
difference: `slot` instead of `sort_order` -- a supplier has exactly
ONE live profile photo and ONE live cover banner, not an ordered
gallery, so there's nothing to sort; there's a fixed pair of named
slots instead.

WHY A SEPARATE TABLE AND NOT JUST THE TWO URL COLUMNS ON
SupplierProfile: the URL columns (business_image_url / cover_image_url)
still exist and are still what everything DISPLAY-facing reads -- but
they only ever hold the CURRENTLY-APPROVED url for each slot. This
table is the upload/scan bookkeeping behind them: it's what the
orphan-upload sweep, the stuck-media sweep, and the scan webhook all
need a real row to reconcile against, and what lets a replaced image's
old Cloudinary asset be found and cleaned up rather than silently
orphaned. Same split as SupplierOffer.images (the derived, approved-only
list) vs. ProductMedia (the rows behind it).
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db
from src.shared.media.mixins import MediaAssetMixin


class ProfileImageSlot(str, enum.Enum):
    """Same name==value convention as every other enum in this codebase
    (see products/models/product.py's ProductCategory docstring)."""

    # The square/circular business identity photo -- promotes to
    # SupplierProfile.business_image_url on approval.
    PROFILE = "profile"
    # The wide brand-showcase banner shown at the top of the profile --
    # promotes to SupplierProfile.cover_image_url on approval. See that
    # column's own comment for why these two are deliberately separate
    # images, not one reused field.
    COVER = "cover"


class SupplierProfileImage(BaseModel, MediaAssetMixin):
    __tablename__ = "supplier_profile_images"
    __table_args__ = (
        db.Index("ix_supplier_profile_images_profile_id", "supplier_profile_id"),
        # The stuck-media sweep and the scan webhook both query by
        # status -- same index products/models/product_media.py keeps
        # for the identical reason.
        db.Index("ix_supplier_profile_images_scan_status", "scan_status"),
        {"schema": "supplier"},
    )

    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    # ProfileImageSlot value -- a plain string, not a Postgres native
    # enum, matching MediaAssetMixin.scan_status's own reasoning (this
    # domain's schema is "supplier", the mixin lives in shared/media,
    # and a cross-schema named enum type adds real complexity for a
    # two-value column the application layer validates anyway).
    slot = db.Column(db.String(20), nullable=False)
