"""
Upload intent service -- the two calls every domain's own upload flow
makes: create_intent right when a signature is issued, mark_registered
right when the matching register call succeeds. See models.py's own
docstring for the full lifecycle/orphan-protection reasoning.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.shared.media.intents.models import MediaUploadIntent
from src.shared.media.intents.repositories import MediaUploadIntentRepository

# How long a signed-but-unregistered upload gets before it's treated
# as abandoned. Deliberately more generous than the stuck-PENDING
# sweep's own 30-minute window (jobs/stuck_media_sweep.py) -- these are
# different problems. That sweep is about a scan result never arriving
# for something that WAS registered; this one is about registration
# itself never happening for something that MAY have been uploaded.
# Retries, slow connections, and a supplier switching apps mid-upload
# all need real room here before this backend concludes the client
# genuinely abandoned it.
INTENT_GRACE_PERIOD_MINUTES = 60


def create_intent(account_id: str | UUID, domain: str, cloudinary_public_id: str) -> MediaUploadIntent:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=INTENT_GRACE_PERIOD_MINUTES)
    return MediaUploadIntentRepository.create(account_id, domain, cloudinary_public_id, expires_at)


def mark_registered(cloudinary_public_id: str) -> None:
    intent = MediaUploadIntentRepository.get_by_public_id(cloudinary_public_id)
    if intent is None:
        # Nothing to mark -- e.g. bulk import's own upload_and_register_
        # from_bytes never goes through the signed-upload flow at all
        # (this backend uploads the bytes itself in one step), so no
        # intent was ever created for it. Not an error condition.
        return
    MediaUploadIntentRepository.mark_registered(intent)


def cancel_intent(cloudinary_public_id: str) -> None:
    """For the case where THIS BACKEND deletes the asset immediately
    (e.g. register_uploaded_media rejecting an oversized file and
    cleaning it up right there) -- marks the intent resolved now
    rather than leaving it ISSUED for the sweep to discover up to
    INTENT_GRACE_PERIOD_MINUTES later. Reuses the CANCELLED status
    (see models.py's own docstring: reserved for exactly this kind of
    "resolved, but not via a successful registration" case)."""
    intent = MediaUploadIntentRepository.get_by_public_id(cloudinary_public_id)
    if intent is None:
        return
    MediaUploadIntentRepository.mark_cancelled(intent)
