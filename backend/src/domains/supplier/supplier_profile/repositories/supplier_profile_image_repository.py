"""
SupplierProfileImageRepository -- pure SQL, no business rules, same
rule as every other repository in this codebase. Method shapes mirror
products/repositories/product_media_repository.py (create_pending /
get_by_public_id / apply_scan_status / soft-delete), minus the
gallery-specific queries a single-image-per-slot model has no use for.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.domains.supplier.supplier_profile.models.supplier_profile_image import SupplierProfileImage
from src.extensions import db
from src.shared.media.mixins import MediaScanStatus


class SupplierProfileImageRepository:
    @staticmethod
    def get_by_public_id(cloudinary_public_id: str) -> Optional[SupplierProfileImage]:
        return SupplierProfileImage.query.filter_by(
            cloudinary_public_id=cloudinary_public_id, is_deleted=False
        ).first()

    @staticmethod
    def get_current_for_slot(
        supplier_profile_id: str | UUID, slot: str
    ) -> Optional[SupplierProfileImage]:
        """The live row for a slot -- newest non-deleted, whatever its
        scan_status. Used to supersede-and-clean-up the previous image
        when a new one is uploaded to the same slot."""
        return (
            SupplierProfileImage.query.filter_by(
                supplier_profile_id=supplier_profile_id, slot=slot, is_deleted=False
            )
            .order_by(SupplierProfileImage.created_at.desc())
            .first()
        )

    @staticmethod
    def create_pending(
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
        image = SupplierProfileImage(
            supplier_profile_id=supplier_profile_id,
            slot=slot,
            cloudinary_public_id=cloudinary_public_id,
            secure_url=secure_url,
            resource_type=resource_type,
            format=format,
            width=width,
            height=height,
            bytes=bytes_,
            scan_status=MediaScanStatus.PENDING.value,
        )
        db.session.add(image)
        db.session.commit()
        return image

    @staticmethod
    def apply_scan_status(
        image: SupplierProfileImage, status: str, scan_provider: str, raw_result: Optional[str]
    ) -> SupplierProfileImage:
        image.scan_status = status
        image.scan_provider = scan_provider
        image.scan_result = raw_result
        image.scanned_at = datetime.now(timezone.utc)
        db.session.commit()
        return image

    @staticmethod
    def soft_delete(image: SupplierProfileImage) -> None:
        image.soft_delete()
        db.session.commit()
