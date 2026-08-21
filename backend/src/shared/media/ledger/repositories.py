"""
MediaUploadLedgerRepository -- pure SQL, no business rules, same rule
as every other repository in this codebase.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.extensions import db
from src.shared.media.ledger.models import MediaUploadRecord


class MediaUploadLedgerRepository:
    @staticmethod
    def record(account_id: str | UUID, domain: str, num_bytes: int) -> MediaUploadRecord:
        record = MediaUploadRecord(account_id=account_id, domain=domain, bytes=num_bytes)
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def total_bytes_since(account_id: str | UUID, since: datetime) -> int:
        """Sums across EVERY domain for this account -- the whole
        point of this table living in shared/media rather than one
        domain's own repository."""
        total = (
            db.session.query(db.func.coalesce(db.func.sum(MediaUploadRecord.bytes), 0))
            .filter(MediaUploadRecord.account_id == account_id, MediaUploadRecord.created_at >= since)
            .scalar()
        )
        return int(total or 0)
