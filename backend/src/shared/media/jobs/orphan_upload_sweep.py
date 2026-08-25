"""
Sweeps media_upload_intents still ISSUED past their own grace period --
these are real orphans: a signature was handed out, the client may
have genuinely uploaded to Cloudinary, but the register call never
arrived (crash, dropped connection, abandoned upload). Deletes the
actual Cloudinary asset (safe even if it was never really uploaded --
Cloudinary's own delete is a no-op on a missing asset) and marks the
intent EXPIRED.

DISTINCT FROM stuck_media_sweep.py -- that job handles a REGISTERED
row whose scan result never arrived; this one handles a signature that
never even got registered. Two different failure points in the same
overall pipeline, two different sweeps, same overall discipline
(nothing sits in limbo forever with no path forward).

DOMAIN-AGNOSTIC -- reads media_upload_intents directly, no import from
products/ at all. A future profile-photo or verification-document
domain gets this exact same protection for free, no second sweep job
to write.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.shared.audit.audit import publish
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditStatus
from src.shared.audit.event_types.supplier import SupplierAuditEvent
from src.shared.media.intents.repositories import MediaUploadIntentRepository
from src.shared.media.providers.composition import get_media_provider
from src.shared.scheduling.scheduling_types import JobResult

logger = logging.getLogger(__name__)


def run() -> JobResult:
    now = datetime.now(timezone.utc)
    orphans = MediaUploadIntentRepository.list_expired_still_issued(now)

    provider = get_media_provider()
    cleaned = 0

    for intent in orphans:
        try:
            provider.delete_asset(intent.cloudinary_public_id)
        except Exception:  # noqa: BLE001 - a delete failure must not stop the rest of the sweep
            logger.exception(
                "orphan upload sweep: failed to delete asset %s, marking expired anyway",
                intent.cloudinary_public_id,
            )

        MediaUploadIntentRepository.mark_expired(intent)
        cleaned += 1

        publish(
            AuditEvent(
                event_name=SupplierAuditEvent.MEDIA_ORPHAN_ASSET_CLEANED,
                domain=AuditDomain.PLATFORM,
                status=AuditStatus.SUCCESS,
                metadata={
                    "account_id": str(intent.account_id),
                    "upload_domain": intent.domain,
                    "cloudinary_public_id": intent.cloudinary_public_id,
                },
            )
        )

    if cleaned:
        logger.warning("orphan upload sweep: cleaned %d abandoned upload(s)", cleaned)

    return JobResult(success=True, count=cleaned)
