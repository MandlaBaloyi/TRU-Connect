"""
MediaUploadRecord -- one row per successfully registered upload,
regardless of which domain triggered it (Products today; a future
profile-photo or verification-document domain later). This is the
piece a purely per-domain limit can't provide: an account that stays
under Products' own tier limit, and under a future profile-photo
domain's own limit, and under a future verification-doc domain's own
limit, INDIVIDUALLY, could still be abusing all three AT ONCE. Only a
shared, cross-domain ledger catches that pattern -- it lives in
shared/media specifically because this is the one place that
genuinely sees every domain's uploads.

Lives in its OWN "media" schema, not "supplier" -- this table will
record uploads from business accounts too (profile photos, proof of
payment) the moment those domains exist; putting it in "supplier"
would be wrong from day one.

account_id IS DELIBERATELY GENERIC, NOT supplier_profile_id -- once a
business-role upload exists, this same table needs to record THAT
account's usage too. No FK to any one domain's own account table,
matching the pattern already established for cross-cutting concerns
(audit_events has the same generic user_id shape rather than a
supplier_profile_id FK).
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class MediaUploadRecord(BaseModel):
    __tablename__ = "media_upload_records"
    __table_args__ = (
        db.Index("ix_media_upload_records_account_id_created_at", "account_id", "created_at"),
        {"schema": "media"},
    )

    account_id = db.Column(UUID(as_uuid=True), nullable=False)
    domain = db.Column(db.String(50), nullable=False)  # "products", "profile", "verification", ...
    bytes = db.Column(db.Integer, nullable=False)
