"""
MediaUploadIntentRepository -- pure SQL, no business rules, same rule
as every other repository in this codebase.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from src.extensions import db
from src.shared.media.intents.models import MediaUploadIntent, MediaUploadIntentStatus


class MediaUploadIntentRepository:
    @staticmethod
    def create(
        account_id: str | UUID, domain: str, cloudinary_public_id: str, expires_at: datetime
    ) -> MediaUploadIntent:
        intent = MediaUploadIntent(
            account_id=account_id,
            domain=domain,
            cloudinary_public_id=cloudinary_public_id,
            status=MediaUploadIntentStatus.ISSUED.value,
            expires_at=expires_at,
        )
        db.session.add(intent)
        db.session.commit()
        return intent

    @staticmethod
    def get_by_public_id(cloudinary_public_id: str) -> Optional[MediaUploadIntent]:
        return MediaUploadIntent.query.filter_by(cloudinary_public_id=cloudinary_public_id).first()

    @staticmethod
    def mark_registered(intent: MediaUploadIntent) -> MediaUploadIntent:
        intent.status = MediaUploadIntentStatus.REGISTERED.value
        intent.registered_at = datetime.now(timezone.utc)
        db.session.commit()
        return intent

    @staticmethod
    def mark_expired(intent: MediaUploadIntent) -> MediaUploadIntent:
        intent.status = MediaUploadIntentStatus.EXPIRED.value
        db.session.commit()
        return intent

    @staticmethod
    def mark_cancelled(intent: MediaUploadIntent) -> MediaUploadIntent:
        intent.status = MediaUploadIntentStatus.CANCELLED.value
        db.session.commit()
        return intent

    @staticmethod
    def list_expired_still_issued(now: datetime) -> List[MediaUploadIntent]:
        """The sweep job's own query -- everything still ISSUED whose
        grace period has passed. Never touches REGISTERED/EXPIRED/
        CANCELLED rows."""
        return MediaUploadIntent.query.filter(
            MediaUploadIntent.status == MediaUploadIntentStatus.ISSUED.value,
            MediaUploadIntent.expires_at < now,
        ).all()
