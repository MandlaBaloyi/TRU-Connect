"""
Letting an order finish.

NOTHING EVER MOVED AN ORDER OUT OF CONFIRMED (V2_14 Part 1). A shop
ordered, a supplier accepted, stock changed hands in the real world,
and the record sat at CONFIRMED forever -- so "open orders" meant
"every order ever accepted", and no dispute could rest on anything,
because there was no moment the platform recognised as finished.

TWO TRANSITIONS HERE, AND NEITHER NEEDED A DECISION FROM MANDLA. The
five questions V2_14 leaves open are all about the EDGES -- how long a
timeout runs, whether a direct order can be disputed, who may cancel
after confirmation, when a dispute becomes visible. The middle of the
flow is not in doubt:

    SUPPLIER MARKS DISPATCHED   they know when it left them
    BUSINESS CONFIRMS RECEIVED  the strong signal, and the only one a
                                dispute can rest on

WHAT IS DELIBERATELY ABSENT: the timeout sweep (how many days is
question 1), DISPUTED (questions 2 and 5), and any change to who may
cancel (question 4). Building those would be answering his questions by
implementing one option, which is the least visible way to make a
product decision.

DISPATCH IS OPTIONAL AND THE DESIGN MUST NOT NEED IT. Most informal
suppliers will never tap it. An order going straight from CONFIRMED to
COMPLETED is the ordinary path, not a degraded one, which is why
confirm_received accepts either status rather than requiring dispatch
first.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.domains.network.orders.errors import (
    OrderNotCompletableError,
    OrderNotDispatchableError,
    OrderNotFoundError,
)
from src.domains.network.orders.models.stock_order import (
    StockOrderCompletedBy,
    StockOrderStatus,
)
from src.domains.network.orders.models.stock_order_event import (
    StockOrderEventActor,
    StockOrderEventType,
)
from src.domains.network.orders.repositories.stock_order_repository import (
    StockOrderRepository,
)
from src.domains.network.orders.services import order_event_service
from src.extensions import db

#: An order the business may still confirm receiving. DISPATCHED is
#: included because dispatch is optional -- requiring it would make a
#: supplier who never taps anything able to block their customer from
#: closing their own order.
COMPLETABLE_FROM = (StockOrderStatus.CONFIRMED, StockOrderStatus.DISPATCHED)


def mark_dispatched(supplier_profile_id: str | UUID, order_id: str | UUID) -> dict:
    """CONFIRMED -> DISPATCHED. The supplier says it has left them.

    NOT A CLAIM THAT IT ARRIVED, and the distinction is the whole
    reason this is a separate state from COMPLETED. The supplier knows
    when stock left their yard; only the shop knows when it reached
    theirs.
    """
    order = StockOrderRepository.get_by_id_for_supplier(order_id, supplier_profile_id)
    if not order:
        raise OrderNotFoundError("Order not found.")
    if order.status != StockOrderStatus.CONFIRMED:
        raise OrderNotDispatchableError(
            "Only a confirmed order can be marked as on its way."
        )

    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    previous = order.status
    order.status = StockOrderStatus.DISPATCHED
    order.dispatched_at = datetime.now(timezone.utc)

    order_event_service.record(
        order,
        StockOrderEventType.DISPATCHED,
        from_status=previous,
        actor=StockOrderEventActor.SUPPLIER,
        actor_user_id=supplier.supplier_id if supplier else None,
    )
    db.session.commit()
    return {"id": str(order.id), "status": order.status.value}


def confirm_received(
    business_id: str | UUID,
    supplier_profile_id: str | UUID,
    order_id: str | UUID,
) -> dict:
    """CONFIRMED or DISPATCHED -> COMPLETED, by the business.

    THE STRONG SIGNAL. completed_by records BUSINESS precisely so that
    this can never be confused with the timeout completing it later --
    a SYSTEM completion means nobody objected in time and is not
    evidence that anything arrived. Collapsing the two would destroy the
    only distinction that matters when somebody says it never came.

    ONLY THE BUSINESS MAY CALL THIS. The supplier is already paid on
    the digital rail, it flatters their own statistics, and nobody is
    checking -- so their incentive points the wrong way at exactly the
    moment the record starts mattering.
    """
    # SCOPED BY SUPPLIER TOO, matching every other business-side order
    # route (/checkout/suppliers/<id>/history/<id>). It also means an
    # order id alone is never enough to touch somebody else's order.
    order = StockOrderRepository.get_by_id_for_business_and_supplier(
        order_id, business_id, supplier_profile_id
    )
    if not order:
        raise OrderNotFoundError("Order not found.")
    if order.status not in COMPLETABLE_FROM:
        raise OrderNotCompletableError("This order is already closed.")

    previous = order.status
    order.status = StockOrderStatus.COMPLETED
    order.completed_at = datetime.now(timezone.utc)
    order.completed_by = StockOrderCompletedBy.BUSINESS

    order_event_service.record(
        order,
        StockOrderEventType.COMPLETED,
        from_status=previous,
        actor=StockOrderEventActor.BUSINESS,
        actor_user_id=str(business_id),
    )
    db.session.commit()
    return {
        "id": str(order.id),
        "status": order.status.value,
        "completedBy": order.completed_by.value,
    }
