"""
ProductMediaService -- orchestrates ownership checks, tier limits, and
folder construction around the generic MediaProvider/signing_service.
Nothing here imports cloudinary directly; only get_media_provider().

apply_scan_result IS THE WEBHOOK'S ACTUAL CALLBACK -- registered via
register_scan_result_handler("tru_connect/products/", apply_scan_result)
at app startup (src/__init__.py). MUST BE IDEMPOTENT: a webhook that's
already been applied (row already APPROVED/REJECTED/ERROR) is a no-op,
not a re-apply -- webhook senders retry, and a duplicate delivery must
never double-process or overwrite a result with a stale retry.
"""
from __future__ import annotations

import uuid
from typing import List, Optional
from uuid import UUID

from src.domains.supplier.products.models.product_media import ProductMedia
from src.domains.supplier.products.repositories.product_media_repository import ProductMediaRepository
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.products.services.errors import ProductNotFoundError
from src.shared.audit.audit import publish
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditEventName, AuditStatus
from src.shared.media.composition import get_media_provider
from src.shared.media.config import MediaConfig
from src.shared.media.errors import PhotoLimitExceededError
from src.shared.media.mixins import MediaScanStatus
from src.shared.media.provider import ScanResult, SignedUpload

FOLDER_PREFIX = "tru_connect/products"

_config = MediaConfig.from_env()


def _build_public_id(supplier_profile_id: str | UUID, product_id: str | UUID) -> str:
    # A random UUID per asset, not the client's own filename --
    # filenames are never trusted as part of a storage path (no
    # extension-based tricks, no collisions, nothing guessable).
    return f"{FOLDER_PREFIX}/{supplier_profile_id}/{product_id}/{uuid.uuid4()}"


def request_upload_signature(product_id: str | UUID, supplier_profile_id: str | UUID, tier: str) -> SignedUpload:
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")

    existing_count = ProductMediaRepository.count_non_rejected_for_product(product_id)
    limit = _config.photo_limit_for_tier(tier)
    if existing_count >= limit:
        raise PhotoLimitExceededError(
            f"Your plan allows up to {limit} photos per product.",
            errors=[f"Your plan allows up to {limit} photos per product."],
        )

    public_id = _build_public_id(supplier_profile_id, product_id)
    return get_media_provider().generate_signed_upload(public_id)


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
    expected_prefix = f"{FOLDER_PREFIX}/{supplier_profile_id}/{product_id}/"
    if not cloudinary_public_id.startswith(expected_prefix):
        raise ProductNotFoundError("Product not found.")

    if bytes_ is not None and bytes_ > _config.max_image_bytes:
        # Reject AND clean up -- never leave an oversized asset sitting
        # in provider storage with no database row pointing at it.
        get_media_provider().delete_asset(cloudinary_public_id)
        raise PhotoLimitExceededError(
            "Image is too large.", errors=[f"Images must be under {_config.max_image_bytes // (1024 * 1024)}MB."]
        )

    existing_count = ProductMediaRepository.count_non_rejected_for_product(product_id)
    sort_order = existing_count

    return ProductMediaRepository.create_pending(
        product_id=product_id,
        cloudinary_public_id=cloudinary_public_id,
        secure_url=secure_url,
        resource_type=resource_type,
        format=format,
        width=width,
        height=height,
        bytes_=bytes_,
        sort_order=sort_order,
    )


def list_approved_media(product_id: str | UUID) -> List[str]:
    """Secure URLs only, ordered -- exactly what products_routes.py's
    own _to_dto needs for the `images` field."""
    return [m.secure_url for m in ProductMediaRepository.list_approved_for_product(product_id)]


def apply_scan_result(result: ScanResult) -> None:
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
                event_name=AuditEventName.PRODUCT_MEDIA_REJECTED,
                domain=AuditDomain.SUPPLIER,
                status=AuditStatus.FAILURE,
                metadata={
                    "product_id": str(media.product_id),
                    "media_id": str(media.id),
                    "cloudinary_public_id": media.cloudinary_public_id,
                },
            )
        )
