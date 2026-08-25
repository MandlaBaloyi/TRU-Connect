"""
ProductMediaRepository -- pure SQL, no business rules, same rule as
every other repository in this codebase.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from src.domains.supplier.products.models.product import Product
from src.domains.supplier.products.models.product_media import ProductMedia
from src.extensions import db
from src.shared.media.mixins import MediaScanStatus


class ProductMediaRepository:
    @staticmethod
    def count_non_rejected_for_product(product_id: str | UUID) -> int:
        """The photo-limit check's own question -- REJECTED media
        doesn't count against a supplier's tier limit (it was never
        really theirs to begin with; letting it consume their photo
        slot would be a real bug, not just unfair)."""
        return ProductMedia.query.filter(
            ProductMedia.product_id == product_id,
            ProductMedia.is_deleted.is_(False),
            ProductMedia.scan_status != MediaScanStatus.REJECTED.value,
        ).count()

    @staticmethod
    def get_by_public_id(cloudinary_public_id: str) -> Optional[ProductMedia]:
        return ProductMedia.query.filter_by(cloudinary_public_id=cloudinary_public_id, is_deleted=False).first()

    @staticmethod
    def get_by_id_and_product(media_id: str | UUID, product_id: str | UUID) -> Optional[ProductMedia]:
        return ProductMedia.query.filter_by(id=media_id, product_id=product_id, is_deleted=False).first()

    @staticmethod
    def list_approved_for_product(product_id: str | UUID) -> List[ProductMedia]:
        """The ONLY query anything business-facing should ever use --
        PENDING/REJECTED/ERROR media is never returned here, matching
        "never expose rejected or unverified media to businesses"."""
        return (
            ProductMedia.query.filter_by(
                product_id=product_id, is_deleted=False, scan_status=MediaScanStatus.APPROVED.value
            )
            .order_by(ProductMedia.sort_order.asc())
            .all()
        )

    @staticmethod
    def create_pending(
        product_id: str | UUID,
        cloudinary_public_id: str,
        secure_url: str,
        resource_type: str,
        format: Optional[str],
        width: Optional[int],
        height: Optional[int],
        bytes_: Optional[int],
        sort_order: int,
    ) -> ProductMedia:
        media = ProductMedia(
            product_id=product_id,
            cloudinary_public_id=cloudinary_public_id,
            secure_url=secure_url,
            resource_type=resource_type,
            format=format,
            width=width,
            height=height,
            bytes=bytes_,
            sort_order=sort_order,
            scan_status=MediaScanStatus.PENDING.value,
        )
        db.session.add(media)
        db.session.commit()
        return media

    @staticmethod
    def apply_scan_status(
        media: ProductMedia, status: str, scan_provider: str, raw_result: Optional[str]
    ) -> ProductMedia:
        media.scan_status = status
        media.scan_provider = scan_provider
        media.scan_result = raw_result
        media.scanned_at = datetime.now(timezone.utc)
        db.session.commit()
        return media

    @staticmethod
    def delete(media: ProductMedia) -> None:
        media.soft_delete()
        db.session.commit()

    @staticmethod
    def list_stuck_pending(older_than: datetime) -> List[ProductMedia]:
        """The stuck-media sweep job's own query -- see
        shared/media/jobs/stuck_media_sweep.py."""
        return ProductMedia.query.filter(
            ProductMedia.scan_status == MediaScanStatus.PENDING.value,
            ProductMedia.is_deleted.is_(False),
            ProductMedia.created_at < older_than,
        ).all()

    @staticmethod
    def list_media_for_deleted_products_older_than(cutoff: datetime) -> List[ProductMedia]:
        """The deleted-product Cloudinary cleanup sweep's own query
        (see products/jobs/deleted_product_media_sweep.py) -- every
        NOT-YET-CLEANED-UP media row (is_deleted=False on the media
        itself) belonging to a product that's been soft-deleted for at
        least the configured grace period. Once a media row's real
        Cloudinary asset is deleted, THIS row is also soft-deleted --
        that tracks "cleaned up", independent of whatever its own
        scan_status was (approved/rejected/pending all get cleaned up
        the same way once the parent product is gone).

        ORDERED BY Product.deleted_at, oldest first -- meaningful now
        that the sweep caps how many PRODUCTS it processes per run
        (see the sweep's own MAX_PRODUCTS_PER_RUN docstring): whatever
        doesn't fit in this run's cap should be whatever's been
        waiting the SHORTEST time, not an arbitrary DB-decided order."""
        return (
            ProductMedia.query.join(Product, ProductMedia.product_id == Product.id)
            .filter(
                ProductMedia.is_deleted.is_(False),
                Product.is_deleted.is_(True),
                Product.deleted_at < cutoff,
            )
            .order_by(Product.deleted_at.asc())
            .all()
        )
