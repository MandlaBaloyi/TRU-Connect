"""
Upload ledger service -- the cross-domain safety net, sitting BEHIND
each domain's own tier check, not instead of it. A domain's own tier
limit (e.g. products/tiers/free.py) is the primary, business-shaped
gate; this is a flat, tier-agnostic backstop that catches an account
abusing MULTIPLE domains at once, each individually under its own
limit. Deliberately conservative and deliberately NOT tier-aware --
shared/media has no business knowing what "Free" means to Products or
to any other domain; it only knows "how many raw bytes has this
account pushed through the platform's media pipeline recently".

record_upload should be called by every domain AFTER a real upload
succeeds (see products/services/product_media_service.py's own call
sites) -- this is accounting, not a pre-check; the actual size/format
gate stays each domain's own responsibility.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.shared.media.errors import MediaUploadQuotaExceededError
from src.shared.media.ledger.repositories import MediaUploadLedgerRepository

# Flat, platform-wide, tier-agnostic daily ceiling -- deliberately
# conservative given today's real Cloudinary Free plan economics (see
# products/tiers/__init__.py's own docstring for the full numbers).
# This is a SAFETY NET, not the primary limit -- raise it once the
# account is on a paid Cloudinary plan, same "tune later, purely by
# changing a number" pattern as every other limit in this build.
DAILY_ACCOUNT_BYTE_QUOTA = 200 * 1024 * 1024  # 200MB/account/day, across ALL domains combined


def check_quota_before_upload(account_id: str | UUID, incoming_bytes: int) -> None:
    since = datetime.now(timezone.utc) - timedelta(days=1)
    used = MediaUploadLedgerRepository.total_bytes_since(account_id, since)
    if used + incoming_bytes > DAILY_ACCOUNT_BYTE_QUOTA:
        raise MediaUploadQuotaExceededError(
            "Daily upload limit reached across all media types -- try again tomorrow.",
            errors=["Daily upload limit reached across all media types."],
        )


def record_upload(account_id: str | UUID, domain: str, num_bytes: int) -> None:
    MediaUploadLedgerRepository.record(account_id, domain, num_bytes)
