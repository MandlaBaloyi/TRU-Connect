"""
Recording what happened to a stock order.

TRANSACTIONAL, NOT BEST-EFFORT -- and this is the one place where this
codebase's usual "never raise" rule for side effects does NOT apply.

The audit trail and the notification queue are side effects: the thing
already happened, and a failure to describe it must not undo it. This
is different. The event log IS the history of the order. If the status
changes and the event does not, the history is not merely incomplete,
it is WRONG -- and wrong in a way nobody notices until somebody asks
why an order is in a state no event explains.

So `record` adds to the session and lets the CALLER'S existing commit
carry it. The event and the state change land together or neither
does. In practice the only way this fails is a database that is down,
in which case the status change was never going to commit either.

  ─────────────────────────────────────────────────────────────────────
  Never call db.session.commit() in here. The caller owns the
  transaction, and stealing it would break exactly the atomicity this
  module exists to provide.
  ─────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.domains.network.orders.models.stock_order_event import (
    StockOrderEvent,
    StockOrderEventActor,
    StockOrderEventType,
)
from src.extensions import db


def record(
    order,
    event_type: StockOrderEventType,
    *,
    from_status,
    actor: StockOrderEventActor,
    actor_user_id: Optional[str | UUID] = None,
    reason: Optional[str] = None,
) -> StockOrderEvent:
    """Append one event. Call AFTER setting order.status, BEFORE commit.

    `from_status` is passed rather than read off the order, because by
    the time this is called the order already holds the NEW status --
    the previous one has to be captured by the caller before it is
    overwritten. Making it an explicit argument is what stops a caller
    silently recording "PENDING -> PENDING".
    """
    event = StockOrderEvent(
        stock_order_id=order.id,
        business_id=order.business_id,
        supplier_profile_id=order.supplier_profile_id,
        event_type=event_type,
        from_status=from_status,
        to_status=order.status,
        actor=actor,
        actor_user_id=actor_user_id,
        reason=(reason or None),
    )
    db.session.add(event)
    return event


def list_for_order(order_id: str | UUID) -> list[StockOrderEvent]:
    """Oldest first -- a history is read in the order it happened."""
    return (
        StockOrderEvent.query.filter_by(stock_order_id=order_id)
        .order_by(StockOrderEvent.occurred_at.asc())
        .all()
    )
