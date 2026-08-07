"""History event data access -- append-only: create and list, never
update or delete, matching the model's own design."""
from __future__ import annotations

import uuid
from typing import List

from src.domains.business.loan_book.models.loan_history_event import LoanHistoryEvent
from src.extensions import db


class HistoryRepository:
    @staticmethod
    def append(event: LoanHistoryEvent) -> LoanHistoryEvent:
        db.session.add(event)
        db.session.flush()
        return event

    @staticmethod
    def list_for_business(business_id: uuid.UUID) -> List[LoanHistoryEvent]:
        return (
            LoanHistoryEvent.query.filter_by(business_id=business_id)
            .order_by(LoanHistoryEvent.occurred_at.desc())
            .all()
        )
