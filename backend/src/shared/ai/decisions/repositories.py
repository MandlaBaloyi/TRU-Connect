"""
AIDecision reads and writes -- the ledger behind the budget ceiling.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

from src.shared.ai.decisions.models import AIDecision, AIDecisionKind
from src.extensions import db


def hash_input(*parts: str) -> str:
    """SHA-256 of the question, so "was this the same call" is
    answerable without storing a supplier's catalogue text forever."""
    digest = hashlib.sha256()
    for part in parts:
        digest.update((part or "").encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


class AIDecisionRepository:
    @staticmethod
    def record(
        *,
        feature: str,
        kind: AIDecisionKind,
        provider: str,
        model: str,
        input_hash: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_input_tokens: int = 0,
        cost_cents: int = 0,
        confidence: Optional[float] = None,
        error: Optional[str] = None,
    ) -> AIDecision:
        """NOT committed here -- the caller batches, the same way
        ImportJobRepository.add_row does, because a 10,000-row file must
        not do 10,000 round trips."""
        decision = AIDecision(
            feature=feature,
            kind=kind,
            provider=provider,
            model=model,
            input_hash=input_hash,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached_input_tokens,
            cost_cents=cost_cents,
            confidence=round(float(confidence), 3) if confidence is not None else None,
            error=(error or None) and error[:300],
        )
        db.session.add(decision)
        return decision

    @staticmethod
    def spend_this_month_cents(now: Optional[datetime] = None) -> int:
        """Everything spent since the first of the current month, UTC.

        SUMMED IN SQL, never by loading rows. This runs BEFORE EVERY PAID
        CALL, so a version that got slower as the ledger grew would make
        the budget check the most expensive part of an import.

        A CALENDAR MONTH, not a rolling 30 days, because that is how the
        person setting the budget thinks about it -- and a ceiling nobody
        can predict the reset of is one they will not trust.
        """
        moment = now or datetime.now(timezone.utc)
        start = moment.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total = (
            db.session.query(db.func.coalesce(db.func.sum(AIDecision.cost_cents), 0))
            .filter(AIDecision.created_at >= start, AIDecision.is_deleted.is_(False))
            .scalar()
        )
        return int(total or 0)
