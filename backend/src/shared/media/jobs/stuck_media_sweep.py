"""
Sweeps product_media rows still PENDING past a real timeout -- webhooks
get delayed, dropped, or the provider can have an outage; without this,
an asset whose webhook never arrives sits invisible-to-everyone forever
with no path forward. Marks it ERROR (not REJECTED -- this backend
never actually learned it failed a scan, only that it never heard
back) and writes an audit entry.

Same pure-job-service contract as every other job in this codebase:
takes no arguments, returns a JobResult, has no idea it's scheduled.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from src.domains.supplier.products.repositories.product_media_repository import ProductMediaRepository
from src.shared.audit.audit import publish
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditStatus
from src.shared.audit.event_types.supplier import SupplierAuditEvent
from src.shared.media.mixins import MediaScanStatus
from src.shared.scheduling.scheduling_types import JobResult

logger = logging.getLogger(__name__)

STUCK_PENDING_TIMEOUT_MINUTES = 30


def run() -> JobResult:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STUCK_PENDING_TIMEOUT_MINUTES)
    stuck = ProductMediaRepository.list_stuck_pending(older_than=cutoff)

    for media in stuck:
        ProductMediaRepository.apply_scan_status(
            media,
            status=MediaScanStatus.ERROR.value,
            scan_provider="cloudinary",
            raw_result="No scan callback received within timeout.",
        )
        publish(
            AuditEvent(
                event_name=SupplierAuditEvent.PRODUCT_MEDIA_REJECTED,
                domain=AuditDomain.SUPPLIER,
                status=AuditStatus.FAILURE,
                metadata={
                    "product_id": str(media.product_id),
                    "media_id": str(media.id),
                    "cloudinary_public_id": media.cloudinary_public_id,
                    "reason": "stuck_pending_timeout",
                },
            )
        )

    if stuck:
        logger.warning("media stuck-pending sweep: marked %d asset(s) ERROR", len(stuck))

    return JobResult(success=True, count=len(stuck))
