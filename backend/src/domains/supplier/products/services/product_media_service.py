"""
ProductMediaService -- orchestrates ownership checks, TIER limits (see
products/tiers/), and folder construction around the generic
MediaProvider. Nothing here imports cloudinary directly; only
get_media_provider().

TIER, NOT A CONFIG DEFAULT -- request_upload_signature and
upload_and_register_from_bytes both call tiers.resolver.get_current_tier
and read every limit (photo count, max upload size, stored dimension,
per-domain) from products/tiers/. Nothing here hardcodes a number --
see that module's own docstring for the full Cloudinary-economics
reasoning behind the actual figures.

LEDGER CHECK IS A SEPARATE, SECOND GATE -- shared/media/ledger's own
cross-domain daily quota is checked IN ADDITION TO the tier limit, not
instead of it. The tier limit is the business rule (what THIS plan
allows in Products); the ledger is the platform-wide safety net
catching an account abusing multiple domains at once. Both must pass.

FOLDER STRUCTURE COMES FROM shared/media/folder_naming.py, NOT A LOCAL
CONSTANT -- see that module's own docstring for the full who-owns-it-
first taxonomy reasoning (confirmed during review): assets are grouped
by supplier/business first, asset type second, so an admin reviewing
one supplier's documents can browse that supplier's whole folder
rather than hunting across a type-first structure.

apply_scan_result IS THE WEBHOOK'S ACTUAL CALLBACK -- registered via
register_scan_result_handler(folder_naming.is_supplier_product_asset,
apply_scan_result) at app startup (src/__init__.py). MUST BE
IDEMPOTENT: a webhook that's already been applied (row already
APPROVED/REJECTED/ERROR) is a no-op, not a re-apply -- webhook senders
retry, and a duplicate delivery must never double-process or overwrite
a result with a stale retry.
"""
from __future__ import annotations

import uuid
from typing import List, Optional
from uuid import UUID

from src.domains.supplier.products.models.product_media import ProductMedia
from src.domains.supplier.products.repositories.product_media_repository import ProductMediaRepository
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.products.services.errors import ProductNotFoundError
from src.domains.supplier.products.tiers import get_products_limits
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

LEDGER_DOMAIN = "products"


def _build_public_id(supplier_profile_id: str | UUID, product_id: str | UUID) -> tuple[str, str]:
    # A random UUID per asset, not the client's own filename --
    # filenames are never trusted as part of a storage path (no
    # extension-based tricks, no collisions, nothing guessable).
    #
    # RETURNS (public_id, asset_folder) -- TWO VALUES, NOT ONE. A real
    # gap found during review: public_id's own path and Cloudinary's
    # separate asset_folder parameter look identical here, but
    # Cloudinary treats them as genuinely independent concepts (see
    # folder_naming.py's own docstring). Setting only public_id's path
    # meant every upload was correctly find-able by search but never
    # actually appeared in the browsable Folders tree at all -- this
    # is the fix, giving callers both values so neither ever gets set
    # without the other again.
    folder = folder_naming.supplier_product_folder(supplier_profile_id, product_id)
    public_id = f"{folder}/{uuid.uuid4()}"
    return public_id, folder


def _check_photo_limit(product_id: str | UUID, limit: int) -> None:
    existing_count = ProductMediaRepository.count_non_rejected_for_product(product_id)
    if existing_count >= limit:
        raise PhotoLimitExceededError(
            f"Your plan allows up to {limit} photos per product.",
            errors=[f"Your plan allows up to {limit} photos per product."],
        )


def request_upload_signature(product_id: str | UUID, supplier_profile_id: str | UUID) -> SignedUpload:
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")

    limits = get_products_limits(get_current_tier(supplier_profile_id))
    _check_photo_limit(product_id, limits.photos_per_product)
    # Ledger check happens at REGISTRATION time (once real bytes/size
    # are known), not here -- signing itself costs nothing and commits
    # to nothing; see register_uploaded_media's own call.

    public_id, asset_folder = _build_public_id(supplier_profile_id, product_id)
    # Recorded the moment a signature is issued, BEFORE any real file
    # exists -- see intents/models.py's own docstring. If the client
    # genuinely uploads to Cloudinary but the register call below never
    # arrives (crash, dropped connection), this row is what lets the
    # orphan sweep find and clean up that asset -- without it, an asset
    # with zero database awareness would sit in Cloudinary forever.
    create_intent(supplier_profile_id, LEDGER_DOMAIN, public_id)
    return get_media_provider().generate_signed_upload(public_id, limits.stored_max_dimension_px, asset_folder)


def register_uploaded_media(
    product_id: str | UUID,
    supplier_profile_id: str | UUID,
    cloudinary_public_id: str,
    secure_url: str,
    resource_type: str,
    format: Optional[str],
    width: Optional[int],
    height: Optional[int],
    bytes_: Optional[int],
) -> ProductMedia:
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")

    # Never trust the client's claimed public_id at face value -- it
    # must be exactly inside the folder this backend itself signed for
    # THIS supplier and THIS product. A mismatch here means either a
    # bug or a client trying to register an asset it was never
    # authorized to attach.
    expected_prefix = folder_naming.supplier_product_folder(supplier_profile_id, product_id) + "/"
    if not cloudinary_public_id.startswith(expected_prefix):
        raise ProductNotFoundError("Product not found.")

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

    existing_count = ProductMediaRepository.count_non_rejected_for_product(product_id)

    media = ProductMediaRepository.create_pending(
        product_id=product_id,
        cloudinary_public_id=cloudinary_public_id,
        secure_url=secure_url,
        resource_type=resource_type,
        format=format,
        width=width,
        height=height,
        bytes_=bytes_,
        sort_order=existing_count,
    )
    _auto_approve_if_moderation_disabled(media)

    if bytes_ is not None:
        record_upload(supplier_profile_id, LEDGER_DOMAIN, bytes_)

    # Marks the intent REGISTERED -- a no-op if none exists (see
    # mark_registered's own docstring for why that's fine, not a bug).
    mark_registered(cloudinary_public_id)

    return media


def list_approved_media(product_id: str | UUID) -> List[str]:
    """Secure URLs only, ordered -- exactly what products_routes.py's
    own _to_dto needs for the `images` field."""
    return [m.secure_url for m in ProductMediaRepository.list_approved_for_product(product_id)]


def upload_and_register_from_bytes(product_id: str | UUID, supplier_profile_id: str | UUID, file_bytes: bytes) -> ProductMedia:
    """Bulk import's own path -- see MediaProvider.upload_asset's own
    docstring for why this backend uploads bytes itself here instead
    of the signed-client-upload flow every other caller uses. Ownership,
    the tier photo limit, the tier size limit, AND the ledger quota are
    all enforced identically to the signed-upload path; only the
    transport differs.
    """
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")

    limits = get_products_limits(get_current_tier(supplier_profile_id))
    _check_photo_limit(product_id, limits.photos_per_product)

    num_bytes = len(file_bytes)
    if num_bytes > limits.max_image_upload_bytes:
        raise PhotoLimitExceededError(
            "Image is too large.",
            errors=[f"Images must be under {limits.max_image_upload_bytes // (1024 * 1024)}MB."],
        )
    check_quota_before_upload(supplier_profile_id, num_bytes)

    existing_count = ProductMediaRepository.count_non_rejected_for_product(product_id)
    public_id, asset_folder = _build_public_id(supplier_profile_id, product_id)
    uploaded = get_media_provider().upload_asset(public_id, file_bytes, limits.stored_max_dimension_px, asset_folder)

    media = ProductMediaRepository.create_pending(
        product_id=product_id,
        cloudinary_public_id=uploaded.public_id,
        secure_url=uploaded.secure_url,
        resource_type=uploaded.resource_type,
        format=uploaded.format,
        width=uploaded.width,
        height=uploaded.height,
        bytes_=uploaded.bytes,
        sort_order=existing_count,
    )
    _auto_approve_if_moderation_disabled(media)

    record_upload(supplier_profile_id, LEDGER_DOMAIN, uploaded.bytes or num_bytes)
    return media


def _auto_approve_if_moderation_disabled(media: ProductMedia) -> None:
    """Moderation is a real, deliberate toggle (MediaConfig.
    moderation_enabled) -- if it's off, no scan was ever requested for
    this upload, and Cloudinary will never call back with a result.
    Leaving the row at PENDING in that case would mean it NEVER
    becomes visible, silently -- not a safe default, and not what
    "turn scanning off" should mean. When moderation is off, media is
    trusted immediately instead. This is a genuine trade-off the
    account is making on purpose (see products/tiers/ and the wider
    Cloudinary-cost discussion this toggle came out of), not a silent
    security downgrade -- scan_provider="none" makes that explicit in
    the stored record itself."""
    if get_media_provider().is_moderation_enabled():
        return
    ProductMediaRepository.apply_scan_status(
        media, status=MediaScanStatus.APPROVED.value, scan_provider="none", raw_result="Moderation disabled at registration time."
    )


def apply_scan_result(result: ScanResult) -> None:
    if result.status == "IGNORED":
        # Not a real scan verdict -- e.g. Cloudinary's own "upload"
        # notification, confirmed via a real payload during device
        # testing (see ScanResult's own docstring). Nothing to look up
        # or update; checked first so this costs zero DB queries.
        return

    media = ProductMediaRepository.get_by_public_id(result.public_id)
    if media is None:
        return  # Nothing registered under this public_id -- not this domain's asset.

    if media.scan_status != MediaScanStatus.PENDING.value:
        return  # Already terminal -- idempotent no-op, see this function's own docstring.

    ProductMediaRepository.apply_scan_status(
        media, status=result.status, scan_provider=result.provider, raw_result=result.raw_result
    )

    if result.status == MediaScanStatus.REJECTED.value:
        publish(
            AuditEvent(
                event_name=SupplierAuditEvent.PRODUCT_MEDIA_REJECTED,
                domain=AuditDomain.SUPPLIER,
                status=AuditStatus.FAILURE,
                metadata={
                    "product_id": str(media.product_id),
                    "media_id": str(media.id),
                    "cloudinary_public_id": media.cloudinary_public_id,
                },
            )
        )
