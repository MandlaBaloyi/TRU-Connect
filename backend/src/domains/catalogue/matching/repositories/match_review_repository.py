"""
MatchReview writes -- every proposal the platform made, applied or not.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.domains.catalogue.matching.models.match_review import MatchReview, ReviewStatus
from src.extensions import db


class MatchReviewRepository:
    @staticmethod
    def record(
        *,
        supplier_offer_id: Optional[str | UUID],
        source_text: str,
        proposed_product_id: Optional[str | UUID],
        tier: str,
        confidence: float,
        reason: str,
        status: ReviewStatus,
        evidence: Optional[dict] = None,
        decided_by_source: str = "SYSTEM",
    ) -> MatchReview:
        """NOT committed here -- the caller batches, the same way
        ImportJobRepository.add_row does, because a 10,000-row file must
        not do 10,000 round trips."""
        review = MatchReview(
            supplier_offer_id=supplier_offer_id,
            source_text=(source_text or "")[:300],
            proposed_product_id=proposed_product_id,
            tier=tier,
            confidence=round(float(confidence), 3),
            reason=(reason or "")[:300],
            status=status,
            # `or {}` rather than a mutable default, and never None: the
            # column is NOT NULL so that "no evidence recorded" and "an
            # older row from before evidence existed" are the same empty
            # object rather than two different absences to handle.
            evidence=evidence or {},
            decided_by_source=decided_by_source,
        )
        db.session.add(review)
        return review

    @staticmethod
    def list_pending(limit: int = 100) -> List[MatchReview]:
        """The backlog waiting for the admin control centre that does not
        exist yet. Ordered by confidence descending: the most likely
        matches are the quickest for a reviewer to confirm, so the queue
        gets shorter fastest from that end."""
        return (
            MatchReview.query.filter_by(status=ReviewStatus.PENDING, is_deleted=False)
            .order_by(MatchReview.confidence.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def count_by_status() -> dict:
        rows = (
            db.session.query(MatchReview.status, db.func.count(MatchReview.id))
            .filter(MatchReview.is_deleted.is_(False))
            .group_by(MatchReview.status)
            .all()
        )
        return {status.value: count for status, count in rows}
