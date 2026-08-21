"""
MediaAssetMixin -- the reusable column set for any domain's own
media-attachment table. Confirmed during planning: NOT a generic
polymorphic table with an (owner_type, owner_id) pair -- that breaks
real referential integrity. Instead, each domain that needs media
(products today; profile photos, verification documents, supplier
branding later) builds its OWN table using this mixin plus its own
real foreign key to whatever it actually belongs to (product_id here,
user_id for a future profile_media, etc.). The SCHEMA is defined once;
the TABLE is not shared.

scan_status is the whole point of "treat uploaded media as untrusted
until scanning has completed" -- PENDING is the only state a freshly
registered upload can be in; nothing becomes visible to anyone outside
the uploading account until a webhook moves it to APPROVED.

scan_status IS A PLAIN STRING, NOT A POSTGRES NATIVE ENUM -- unlike
ProductCategory/ProductUnit/LowStockAlertChannel elsewhere in this
codebase. Those live on ONE table in ONE schema each; this mixin is
meant to be reused across DIFFERENT tables that may live in different
schemas (product_media in supplier, a future profile_media likely in
auth), and Postgres enum types are schema-scoped -- reusing one named
type across schemas via a mixin adds real complexity for a column
whose valid values (see MediaScanStatus below) are just as safely
enforced at the application layer.
"""
from __future__ import annotations

import enum

from src.extensions import db


class MediaScanStatus(str, enum.Enum):
    """Same name==value convention as every other enum in this
    codebase (see products/models/product.py's own ProductCategory
    docstring for why)."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


class MediaAssetMixin:
    """Mixed in alongside BaseModel, not instead of it -- concrete
    tables get id/created_at/updated_at/is_deleted from BaseModel as
    normal, plus these columns from here. See products/models/
    product_media.py for the concrete usage."""

    cloudinary_public_id = db.Column(db.String(500), nullable=False, unique=True)
    secure_url = db.Column(db.String(1000), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False, default="image")
    format = db.Column(db.String(20), nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    bytes = db.Column(db.Integer, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    scan_status = db.Column(db.String(20), nullable=False, default=MediaScanStatus.PENDING.value)
    scan_provider = db.Column(db.String(50), nullable=True)
    scan_result = db.Column(db.Text, nullable=True)
    scanned_at = db.Column(db.DateTime(timezone=True), nullable=True)
