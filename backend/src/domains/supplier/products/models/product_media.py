"""
ProductMedia -- product photos. Real FK to products.id, not a
polymorphic owner column -- confirmed during planning as the specific
reason this table lives in products/, not shared/media/ (see
shared/media/mixins.py's own docstring for the full reasoning).

sort_order IS the "which photo is the cover" mechanism -- position 0
is the cover image, matching the frontend's own SupplierOffer.images: ORDERED
array convention exactly (no separate isPrimary flag on either side).
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db
from src.shared.media.mixins import MediaAssetMixin


class ProductMedia(BaseModel, MediaAssetMixin):
    __tablename__ = "product_media"
    __table_args__ = (
        db.Index("ix_product_media_product_id", "product_id"),
        db.Index("ix_product_media_scan_status", "scan_status"),  # the stuck-media sweep job's own query
        {"schema": "supplier"},
    )

    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey("supplier.supplier_offers.id"), nullable=False)
