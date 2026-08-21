"""
MediaUploadIntent -- closes the orphan-upload gap identified during
review: a signature can be issued, the client can genuinely upload to
Cloudinary, and then the register call can simply never happen (app
crash, network drop, closed tab). Without this table, that asset
exists on Cloudinary with ZERO database awareness of it -- the
existing stuck-PENDING sweep can't find it, because that sweep only
looks at rows that already exist in product_media, and this asset
never got one.

A row here is created the moment a signature is issued (ISSUED),
before any real file exists -- see product_media_service's own
request_upload_signature docstring for the call site. It moves to
REGISTERED the moment the matching register call succeeds. Anything
still ISSUED past its own expires_at is a real orphan: the sweep job
(jobs/orphan_upload_sweep.py) deletes the actual Cloudinary asset and
marks the row EXPIRED.

THE SWEEP ONLY EVER ACTS ON A public_id IT FINDS IN THIS TABLE --
never a blind scan of Cloudinary's own storage. This is what makes
"don't delete anything under tru_connect/ that this backend didn't
itself issue" true by construction rather than something the sweep
has to be careful about separately.

GENERIC ON PURPOSE, SAME SHAPE AS THE LEDGER (ledger/models.py) --
account_id/domain, not supplier_profile_id/product_id. A future
profile-photo or verification-document upload needs the identical
orphan protection; this table (and its one sweep job) serves all of
them, not just Products.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class MediaUploadIntentStatus(str, enum.Enum):
    ISSUED = "ISSUED"
    REGISTERED = "REGISTERED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"  # not set by anything yet -- reserved for a future explicit client-cancel action


class MediaUploadIntent(BaseModel):
    __tablename__ = "media_upload_intents"
    __table_args__ = (
        db.Index("ix_media_upload_intents_status_expires_at", "status", "expires_at"),
        {"schema": "media"},
    )

    account_id = db.Column(UUID(as_uuid=True), nullable=False)
    domain = db.Column(db.String(50), nullable=False)  # "products", "profile", "verification", ...
    cloudinary_public_id = db.Column(db.String(500), nullable=False, unique=True)
    status = db.Column(
        db.String(20), nullable=False, default=MediaUploadIntentStatus.ISSUED.value
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    registered_at = db.Column(db.DateTime(timezone=True), nullable=True)
