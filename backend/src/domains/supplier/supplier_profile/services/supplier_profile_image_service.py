"""
SupplierProfileImageService -- orchestrates ownership checks, size/quota
limits, and folder construction around the generic MediaProvider for a
supplier's profile photo and cover banner. Nothing here imports
cloudinary directly; only get_media_provider().

Direct counterpart to products/services/product_media_service.py --
same signed-client-upload flow (this backend never carries image
bytes), same upload-intent orphan protection, same cross-domain ledger
backstop, same PENDING -> APPROVED webhook lifecycle. Read that file's
own docstring for the fuller reasoning behind each shared piece.

TWO DIFFERENCES FROM PRODUCTS, both because a profile has a fixed pair
of single-image slots rather than an ordered gallery:

  1. No per-slot photo COUNT limit -- uploading to a slot that already
     has an image REPLACES it (the old row is soft-deleted and its
     Cloudinary asset cleaned up), so "how many" is always 0 or 1 by
     construction. Only the per-image SIZE limit and the cross-domain
     daily byte quota apply.

  2. On approval, the URL is PROMOTED onto SupplierProfile itself
     (business_image_url / cover_image_url) -- that column is what
     every display-facing reader uses; this table is the upload/scan
     bookkeeping behind it. See supplier_profile_image.py's own
     docstring.

TIER LIMITS ARE READ FROM products/tiers FOR NOW -- get_products_limits
already exists as this supplier area's one media-sizing source
(max_image_upload_bytes, stored_max_dimension_px), and FREE's 3MB /
1600px is a sane ceiling for a profile photo too. A dedicated
supplier_profile/tiers module can replace this later without touching
any caller, same "tune later, purely by changing a number" pattern as
every other limit in this build.

apply_scan_result IS THE WEBHOOK'S ACTUAL CALLBACK -- registered via
register_scan_result_handler(folder_naming.is_supplier_profile_asset,
apply_scan_result) at app startup (src/__init__.py). MUST BE
IDEMPOTENT: a row already in a terminal state is a no-op, never a
re-apply -- webhook senders retry.
"""
from __future__ import annotations

import uuid
from typing import Optional
from uuid import UUID

from src.core.exceptions import NotFoundError
from src.domains.supplier.products.tiers import get_products_limits
from src.domains.supplier.supplier_profile.models.supplier_profile import VisibleImageSource
from src.domains.supplier.supplier_profile.models.supplier_profile_image import (
    ProfileImageSlot,
    SupplierProfileImage,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_image_repository import (
    SupplierProfileImageRepository,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.domains.supplier.supplier_profile.services.errors import ProfileValidationError
from src.domains.supplier.tiers.resolver import get_current_tier
from src.shared.audit.audit import publish
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditStatus
from src.shared.audit.event_types.supplier import SupplierAuditEvent
from src.shared.media import folder_naming
from src.shared.media.errors import PhotoLimitExceededError
from src.shared.media.intents.services import cancel_intent, create_intent, mark_registered
from src.shared.media.ledger.services import check_quota_before_upload, record_upload
from src.shared.media.mixins import MediaScanStatus
from src.shared.media.providers.composition import get_media_provider
from src.shared.media.providers.provider import ScanResult, SignedUpload

LEDGER_DOMAIN = "supplier_profile"

_VALID_SLOTS = {s.value for s in ProfileImageSlot}
# Which SupplierProfile column each slot promotes to on approval.
_SLOT_URL_COLUMN = {
    ProfileImageSlot.PROFILE.value: "business_image_url",
    ProfileImageSlot.COVER.value: "cover_image_url",
}


def _validate_slot(slot: str) -> str:
    if slot not in _VALID_SLOTS:
        raise ProfileValidationError(
            "Unknown image slot.", errors=["Image slot must be 'profile' or 'cover'."]
        )
    return slot


def _build_public_id(supplier_profile_id: str | UUID, slot: str) -> tuple[str, str]:
    """RETURNS (public_id, asset_folder) -- two values, not one. See
    folder_naming.py and products/services/product_media_service.py's
    _build_public_id for why Cloudinary treats these as independent
    concepts and both must always be set together."""
    folder = folder_naming.supplier_profile_folder(supplier_profile_id)
    public_id = f"{folder}/{slot}-{uuid.uuid4()}"
    return public_id, folder


def request_upload_signature(supplier_profile_id: str | UUID, slot: str) -> SignedUpload:
    slot = _validate_slot(slot)
    limits = get_products_limits(get_current_tier(supplier_profile_id))

    public_id, asset_folder = _build_public_id(supplier_profile_id, slot)
    # Recorded the moment a signature is issued, BEFORE any real file
    # exists -- if the client uploads to Cloudinary but the register
    # call never arrives, this row is what lets the orphan sweep find
    # and clean up the asset. Same call, same reasoning, as
    # product_media_service.
    create_intent(supplier_profile_id, LEDGER_DOMAIN, public_id)
    return get_media_provider().generate_signed_upload(
        public_id, limits.stored_max_dimension_px, asset_folder
    )


def register_uploaded_image(
    supplier_profile_id: str | UUID,
    slot: str,
    cloudinary_public_id: str,
    secure_url: str,
    resource_type: str,
    format: Optional[str],
    width: Optional[int],
    height: Optional[int],
    bytes_: Optional[int],
) -> SupplierProfileImage:
    slot = _validate_slot(slot)

    # Never trust the client's claimed public_id -- it must be exactly
    # inside the folder this backend itself signed for THIS supplier.
    expected_prefix = folder_naming.supplier_profile_folder(supplier_profile_id) + "/"
    if not cloudinary_public_id.startswith(expected_prefix):
        raise NotFoundError("Image upload not found.", code="PROFILE_IMAGE_NOT_FOUND")

    limits = get_products_limits(get_current_tier(supplier_profile_id))

    if bytes_ is not None and bytes_ > limits.max_image_upload_bytes:
        # Reject AND clean up -- never leave an oversized asset sitting
        # in provider storage with no database row pointing at it.
        get_media_provider().delete_asset(cloudinary_public_id)
        cancel_intent(cloudinary_public_id)
        raise PhotoLimitExceededError(
            "Image is too large.",
            errors=[f"Images must be under {limits.max_image_upload_bytes // (1024 * 1024)}MB."],
        )

    if bytes_ is not None:
        check_quota_before_upload(supplier_profile_id, bytes_)

    # Replace-in-place: a slot holds exactly one live image. Supersede
    # whatever was there (soft-delete the row, best-effort delete its
    # real Cloudinary asset) so the previous upload never becomes an
    # orphan with no row pointing at it.
    _supersede_existing(supplier_profile_id, slot)

    image = SupplierProfileImageRepository.create_pending(
        supplier_profile_id=supplier_profile_id,
        slot=slot,
        cloudinary_public_id=cloudinary_public_id,
        secure_url=secure_url,
        resource_type=resource_type,
        format=format,
        width=width,
        height=height,
        bytes_=bytes_,
    )
    _apply_immediately_if_moderation_disabled(image)

    if bytes_ is not None:
        record_upload(supplier_profile_id, LEDGER_DOMAIN, bytes_)

    mark_registered(cloudinary_public_id)
    return image


def remove_image(supplier_profile_id: str | UUID, slot: str) -> None:
    slot = _validate_slot(slot)
    existing = SupplierProfileImageRepository.get_current_for_slot(supplier_profile_id, slot)
    if existing is not None:
        _best_effort_delete_asset(existing.cloudinary_public_id)
        SupplierProfileImageRepository.soft_delete(existing)

    profile = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if profile is None:
        return
    update_fields: dict = {_SLOT_URL_COLUMN[slot]: None}
    # If the business photo is being removed and it was the one on
    # show, fall back to showing nothing rather than leaving a
    # dangling BUSINESS source pointing at a now-null column.
    if slot == ProfileImageSlot.PROFILE.value and profile.visible_image_source == VisibleImageSource.BUSINESS:
        update_fields["visible_image_source"] = VisibleImageSource.NONE
    SupplierProfileRepository.update(profile, **update_fields)


def apply_scan_result(result: ScanResult) -> None:
    if result.status == "IGNORED":
        # Not a real scan verdict (e.g. Cloudinary's own "upload"
        # notification) -- nothing to look up or update. Checked first
        # so this costs zero DB queries. See ScanResult's own docstring.
        return

    image = SupplierProfileImageRepository.get_by_public_id(result.public_id)
    if image is None:
        return  # Nothing registered under this public_id -- not this domain's asset.

    if image.scan_status != MediaScanStatus.PENDING.value:
        return  # Already terminal -- idempotent no-op.

    SupplierProfileImageRepository.apply_scan_status(
        image, status=result.status, scan_provider=result.provider, raw_result=result.raw_result
    )

    if result.status == MediaScanStatus.APPROVED.value:
        _promote(image)
    elif result.status == MediaScanStatus.REJECTED.value:
        publish(
            AuditEvent(
                event_name=SupplierAuditEvent.SUPPLIER_PROFILE_IMAGE_REJECTED,
                domain=AuditDomain.SUPPLIER,
                status=AuditStatus.FAILURE,
                metadata={
                    "supplier_profile_id": str(image.supplier_profile_id),
                    "image_id": str(image.id),
                    "slot": image.slot,
                    "cloudinary_public_id": image.cloudinary_public_id,
                },
            )
        )


# ---------------------------------------------------------------------------


def _supersede_existing(supplier_profile_id: str | UUID, slot: str) -> None:
    existing = SupplierProfileImageRepository.get_current_for_slot(supplier_profile_id, slot)
    if existing is None:
        return
    _best_effort_delete_asset(existing.cloudinary_public_id)
    SupplierProfileImageRepository.soft_delete(existing)


def _best_effort_delete_asset(public_id: str) -> None:
    try:
        get_media_provider().delete_asset(public_id)
    except Exception:  # noqa: BLE001 -- cleanup must never break the caller
        pass


def _apply_immediately_if_moderation_disabled(image: SupplierProfileImage) -> None:
    """Moderation is a real, deliberate toggle. When it's off, no scan
    was ever requested and Cloudinary will never call back -- leaving
    the row PENDING would mean the image NEVER becomes visible,
    silently. So when moderation is off, the image is trusted
    immediately AND promoted onto the profile. Identical trade-off,
    identical reasoning, as product_media_service's own
    _auto_approve_if_moderation_disabled -- scan_provider="none" makes
    it explicit in the stored record."""
    if get_media_provider().is_moderation_enabled():
        return
    SupplierProfileImageRepository.apply_scan_status(
        image,
        status=MediaScanStatus.APPROVED.value,
        scan_provider="none",
        raw_result="Moderation disabled at registration time.",
    )
    _promote(image)


def _promote(image: SupplierProfileImage) -> None:
    """Writes an APPROVED image's url onto SupplierProfile -- the column
    every display-facing reader actually uses. For the business photo,
    also flips visible_image_source to BUSINESS when nothing was on
    show yet, so an uploaded photo actually renders instead of sitting
    invisible behind the default NONE."""
    profile = SupplierProfileRepository.get_by_id(image.supplier_profile_id)
    if profile is None:
        return

    update_fields: dict = {_SLOT_URL_COLUMN[image.slot]: image.secure_url}
    if (
        image.slot == ProfileImageSlot.PROFILE.value
        and profile.visible_image_source == VisibleImageSource.NONE
    ):
        update_fields["visible_image_source"] = VisibleImageSource.BUSINESS

    SupplierProfileRepository.update(profile, **update_fields)
