"""
Sweeps ProductMedia rows belonging to products that have been soft-
deleted for at least DELETE_GRACE_PERIOD -- deletes the actual
Cloudinary assets (real network calls to a real external service,
which is exactly why this never happens synchronously inside the
delete request itself -- same discipline as every other media
operation in this build) and marks the media rows themselves soft-
deleted too, which is what "already cleaned up" means to this sweep's
own query.

============================================================================
FOR TESTING: DELETE_GRACE_PERIOD below is set to REAL_GRACE_PERIOD (7
days) by default. To test this sweep without waiting 7 real days,
change the line:

    DELETE_GRACE_PERIOD = REAL_GRACE_PERIOD

to:

    DELETE_GRACE_PERIOD = timedelta(minutes=5)

right below, run a real delete, wait 5 minutes, then trigger the
sweep. REMEMBER TO CHANGE IT BACK to REAL_GRACE_PERIOD before this
goes anywhere near production -- nothing else needs to change, this
one line controls the whole grace period.
============================================================================

WHY A GRACE PERIOD THIS LONG, LONGER THAN THE OTHER TWO SWEEPS IN THIS
BUILD -- a full product delete is a much bigger mistake for a supplier
to accidentally trigger than one stuck photo upload; the other two
sweeps in this build (stuck_media_sweep.py: 30 minutes,
orphan_upload_sweep.py: 60 minutes) are cleaning up things that were
never really "there" to begin with. This one is genuinely destroying
real, previously-working assets, so it gets real room to be undone
first (the product row itself is never actually removed -- see
product_service.delete_product's own docstring -- only the real
Cloudinary files are gone for good once this runs).

BATCHED PER PRODUCT, NOT PER PHOTO -- found during a real cost/scale
review: the original version called provider.delete_asset() once per
PHOTO. Every product's own media all shares one dedicated Cloudinary
folder (see folder_naming.py), so this groups media by that shared
folder, deletes an entire product's photos in ONE real batch call
(provider.delete_assets), then removes that now-empty folder in a
second call -- 2 real network calls per product regardless of how many
photos it had, instead of N.

MAX_PRODUCTS_PER_RUN CAPS HOW MUCH WORK A SINGLE RUN DOES -- the real
"protect a single run from growing unbounded" safeguard discussed
during the same review: if a genuinely large backlog of deleted
products ever built up, one run processing all of them could take
longer to finish than the interval between runs. Whatever doesn't fit
in this run's cap is simply picked up by the next one -- nothing is
lost, just deferred, and the repository's own query orders by
Product.deleted_at ascending so the products waiting longest always go
first.

DOES NOT LIVE IN shared/media/jobs/ -- unlike the other two sweeps,
this one is genuinely Products-domain-specific (it has to know what a
"deleted product" means), so it lives here instead, matching the same
"shared/media doesn't know what a product is" discipline this whole
build has followed from Phase 3 onward.
"""
from __future__ import annotations

import logging
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import List

from src.domains.supplier.products.repositories.product_media_repository import ProductMediaRepository
from src.shared.audit.audit import publish
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditStatus
from src.shared.audit.event_types.supplier import SupplierAuditEvent
from src.shared.media.providers.composition import get_media_provider
from src.shared.scheduling.scheduling_types import JobResult

logger = logging.getLogger(__name__)

REAL_GRACE_PERIOD = timedelta(days=7)

# See the module docstring's own "FOR TESTING" block above before
# changing this line.
DELETE_GRACE_PERIOD = REAL_GRACE_PERIOD

# See the module docstring's own "MAX_PRODUCTS_PER_RUN" section above.
MAX_PRODUCTS_PER_RUN = 50


def _folder_for(cloudinary_public_id: str) -> str:
    # public_id is always {folder}/{asset_uuid} by construction (see
    # folder_naming.py) -- the folder is simply everything before the
    # last slash, no separate lookup needed.
    return cloudinary_public_id.rsplit("/", 1)[0]


def run() -> JobResult:
    cutoff = datetime.now(timezone.utc) - DELETE_GRACE_PERIOD
    media_to_clean = ProductMediaRepository.list_media_for_deleted_products_older_than(cutoff)

    # Grouped by shared folder (== by product, since each product owns
    # exactly one folder) -- an OrderedDict preserves the repository's
    # own oldest-deleted-first ordering, which is what makes capping to
    # the first MAX_PRODUCTS_PER_RUN groups below meaningful rather than
    # arbitrary.
    groups: "OrderedDict[str, list]" = OrderedDict()
    for media in media_to_clean:
        groups.setdefault(_folder_for(media.cloudinary_public_id), []).append(media)

    capped_folders = list(groups.keys())[:MAX_PRODUCTS_PER_RUN]

    provider = get_media_provider()
    cleaned = 0

    for folder in capped_folders:
        group = groups[folder]
        public_ids: List[str] = [m.cloudinary_public_id for m in group]

        try:
            provider.delete_assets(public_ids)
        except Exception:  # noqa: BLE001 - a batch failure must not stop other products' cleanup
            logger.exception(
                "deleted product media sweep: failed to batch-delete %d asset(s) in folder %s, marking cleaned up anyway",
                len(public_ids),
                folder,
            )

        try:
            provider.delete_folder(folder)
        except Exception:  # noqa: BLE001 - purely cosmetic cleanup, never worth failing the run over
            logger.info("deleted product media sweep: could not remove empty folder %s (non-fatal)", folder)

        for media in group:
            ProductMediaRepository.delete(media)
            cleaned += 1

            publish(
                AuditEvent(
                    event_name=SupplierAuditEvent.MEDIA_DELETED_PRODUCT_ASSET_CLEANED,
                    domain=AuditDomain.SUPPLIER,
                    status=AuditStatus.SUCCESS,
                    metadata={
                        "product_id": str(media.product_id),
                        "media_id": str(media.id),
                        "cloudinary_public_id": media.cloudinary_public_id,
                    },
                )
            )

    if cleaned:
        logger.warning(
            "deleted product media sweep: cleaned %d asset(s) across %d product(s) (%d product(s) deferred to next run)",
            cleaned,
            len(capped_folders),
            max(0, len(groups) - len(capped_folders)),
        )

    return JobResult(success=True, count=cleaned)
