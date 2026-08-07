"""OrderLineItem data access. Line items are never edited or deleted
independently of their order -- create and list only, matching the
model's own "computed once, immutable" design."""
from __future__ import annotations

import uuid
from typing import List

from src.domains.business.order_book.models.order_line_item import OrderLineItem
from src.extensions import db


class LineItemRepository:
    @staticmethod
    def create_all(items: List[OrderLineItem]) -> List[OrderLineItem]:
        db.session.add_all(items)
        db.session.flush()
        return items

    @staticmethod
    def list_for_order(order_id: uuid.UUID) -> List[OrderLineItem]:
        return OrderLineItem.query.filter_by(order_id=order_id).all()

    @staticmethod
    def list_for_orders(order_ids: List[uuid.UUID]) -> List[OrderLineItem]:
        if not order_ids:
            return []
        return OrderLineItem.query.filter(OrderLineItem.order_id.in_(order_ids)).all()
