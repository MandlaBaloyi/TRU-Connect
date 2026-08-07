"""History event data access -- append-only: create and list, never
update or delete, matching the model's own design and Loan Book's
HistoryRepository exactly."""
from __future__ import annotations

import uuid
from typing import List

from src.domains.business.order_book.models.order_history_event import OrderHistoryEvent
from src.extensions import db


class HistoryRepository:
    @staticmethod
    def append(event: OrderHistoryEvent) -> OrderHistoryEvent:
        db.session.add(event)
        db.session.flush()
        return event

    @staticmethod
    def list_for_business(business_id: uuid.UUID) -> List[OrderHistoryEvent]:
        return (
            OrderHistoryEvent.query.filter_by(business_id=business_id)
            .order_by(OrderHistoryEvent.occurred_at.desc())
            .all()
        )
