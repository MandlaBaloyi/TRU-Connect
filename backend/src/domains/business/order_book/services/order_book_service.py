"""
Order Book business operations.

THE AUTHORIZATION PATTERN, applied consistently everywhere in this
file: every method that touches an existing order or customer takes
business_id as a REQUIRED parameter and calls a repository's
get_by_id(id, business_id) -- which returns None for "doesn't exist" and
"exists but isn't yours" identically. This service turns that None into
OrderBookNotFoundError uniformly. Same pattern as LoanBookService, for
the same reason -- see that file's docstring and
tests/domains/business/order_book/test_ownership.py.

CUSTOMERS ARE ORDER BOOK'S OWN, NOT SHARED WITH LOAN BOOK. Customer
lives in `business.order_book_customers`, a table independent of Loan
Book's `business.customers` (see models/customer.py's docstring for the
full reasoning). Deleting or restoring a customer here has zero effect
on Loan Book, and vice versa -- the two features happen to model "a
customer" the same way, which is not the same thing as sharing one.

MONEY: every amount is a shared.finance.Money instance from the moment
it enters this file to the moment it leaves. An order's line totals and
grand total are computed ONCE at creation (see create_order) and stored
-- unlike Loan Book's outstanding balance, an order's total has nothing
that mutates it after creation in this feature (no editing line items,
no partial payments), so there is no drift to guard against by
re-deriving it on every read.

ORDER NUMBERING: see models/order.py's docstring. order_number is only
unique within (business_id, order_date) -- enforced by a real database
constraint, not just application logic.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from src.domains.business.order_book.models.customer import OrderBookCustomer
from src.domains.business.order_book.repositories.customer_repository import CustomerRepository
from src.domains.business.order_book.models.order import Order, OrderDeletionReason, OrderStatus
from src.domains.business.order_book.models.order_history_event import (
    OrderHistoryEvent,
    OrderHistoryEventType,
)
from src.domains.business.order_book.models.order_line_item import OrderLineItem
from src.domains.business.order_book.repositories.history_repository import HistoryRepository
from src.domains.business.order_book.repositories.line_item_repository import LineItemRepository
from src.domains.business.order_book.repositories.order_repository import OrderRepository
from src.domains.business.order_book.services.errors import (
    OrderBookInvalidTransitionError,
    OrderBookNotFoundError,
    OrderBookValidationError,
)
from src.domains.business.order_book.utils.trash_retention import days_remaining_in_trash
from src.extensions import db
from src.shared.finance import Money, multiply, total

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _today() -> date:
    # UTC calendar date. KNOWN LIMITATION, stated plainly rather than
    # guessed around: the frontend's mock derives "today" from the
    # device's LOCAL timezone (toDateKey() in dailyRevenue.ts), so a
    # business trading late at night near a day boundary could see the
    # backend and the (still-mock) frontend disagree on which day an
    # order landed on until this is reconciled -- either by passing the
    # business's local date explicitly from the client, or by storing a
    # business-level timezone once one exists. Not silently "fixed" by
    # guessing a timezone here.
    return _now().date()


def _record_history(
    business_id: uuid.UUID,
    customer_id: uuid.UUID,
    event_type: OrderHistoryEventType,
    *,
    order_id: Optional[uuid.UUID] = None,
    amount: Optional[Money] = None,
    reason: Optional[str] = None,
) -> None:
    """NEVER THROWS, and runs in a SAVEPOINT rather than the outer
    transaction -- same reasoning, same mechanism, as Loan Book's
    _record_history(). A lost history row is survivable; an order
    failing to save because ITS OWN history entry failed to save would
    not be."""
    try:
        with db.session.begin_nested():
            HistoryRepository.append(OrderHistoryEvent(
                id=uuid.uuid4(),
                business_id=business_id,
                customer_id=customer_id,
                order_id=order_id,
                event_type=event_type,
                amount_cents=amount.minor_units if amount is not None else None,
                reason=reason,
            ))
    except Exception:  # noqa: BLE001
        logger.warning("Failed to record order book history event", exc_info=True)


@dataclass
class OrderLineItemInput:
    description: str
    quantity: int
    unit_price: Money


@dataclass
class OrderView:
    """The API/service-layer answer to 'what does this order look
    like' -- line items, total, AND customer bundled together, matching
    the frontend's OrderView shape exactly. Customer is fetched and
    attached here (not left for the route layer to guess at) so every
    order response -- list, single, whatever -- carries enough to
    render a customer name without a second round-trip."""

    order: Order
    customer: OrderBookCustomer
    line_items: List[OrderLineItem] = field(default_factory=list)


def _to_view(order: Order) -> Optional[OrderView]:
    customer = CustomerRepository.get_by_id(order.customer_id, order.business_id)
    if customer is None:
        return None  # customer deleted independently; defensive, shouldn't happen in practice
    return OrderView(order=order, customer=customer, line_items=LineItemRepository.list_for_order(order.id))


def _to_views(orders: List[Order]) -> List[OrderView]:
    if not orders:
        return []
    business_id = orders[0].business_id
    customer_ids = {o.customer_id for o in orders}
    customers_by_id = {
        c.id: c for c in OrderBookCustomer.query.filter(
            OrderBookCustomer.id.in_(customer_ids), OrderBookCustomer.business_id == business_id
        ).all()
    }
    all_items = LineItemRepository.list_for_orders([o.id for o in orders])
    items_by_order: Dict[uuid.UUID, List[OrderLineItem]] = {}
    for item in all_items:
        items_by_order.setdefault(item.order_id, []).append(item)
    views = []
    for o in orders:
        customer = customers_by_id.get(o.customer_id)
        if customer is None:
            continue  # defensive, same reasoning as _to_view
        views.append(OrderView(order=o, customer=customer, line_items=items_by_order.get(o.id, [])))
    return views


def _to_view_or_raise(order: Order) -> OrderView:
    view = _to_view(order)
    if view is None:
        raise OrderBookNotFoundError("Order not found.")
    return view


class OrderBookService:
    # --- Customers (Order Book's own — see module docstring) -----

    @staticmethod
    def get_customer(business_id: uuid.UUID, customer_id: uuid.UUID) -> OrderBookCustomer:
        customer = CustomerRepository.get_by_id(customer_id, business_id)
        if customer is None:
            raise OrderBookNotFoundError("Customer not found.")
        return customer

    @staticmethod
    def search_customers(business_id: uuid.UUID, term: str) -> List[OrderBookCustomer]:
        if not term or not term.strip():
            return []
        return CustomerRepository.search(business_id, term.strip())

    @staticmethod
    def _resolve_or_create_customer(
        business_id: uuid.UUID,
        customer_id: Optional[uuid.UUID],
        new_customer_name: Optional[str],
        new_customer_phone: Optional[str],
    ) -> OrderBookCustomer:
        if customer_id is not None:
            # Ownership check happens by construction: get_customer()
            # can only ever return a customer that belongs to
            # business_id -- a caller cannot create an order against
            # someone else's customer even by supplying a real id.
            return OrderBookService.get_customer(business_id, customer_id)

        if not new_customer_name or not new_customer_name.strip():
            raise OrderBookValidationError("Customer name is required.", field="newCustomerName")

        now = _now()
        customer = OrderBookCustomer(
            id=uuid.uuid4(),
            business_id=business_id,
            name=new_customer_name.strip(),
            phone=new_customer_phone.strip() if new_customer_phone else None,
            first_recorded_at=now,
            last_transaction_at=now,
        )
        CustomerRepository.create(customer)
        _record_history(business_id, customer.id, OrderHistoryEventType.CUSTOMER_CREATED)
        return customer

    @staticmethod
    def delete_customer(business_id: uuid.UUID, customer_id: uuid.UUID, reason: Optional[str] = None) -> None:
        """Soft-deletes the customer. Does NOT cascade to their Order
        Book orders -- an order already placed is a historical fact
        worth keeping visible even if the customer record itself is
        removed. Fully independent of Loan Book: this table, this
        row, this delete -- nothing crosses over."""
        customer = CustomerRepository.get_by_id(customer_id, business_id)
        if customer is None:
            raise OrderBookNotFoundError("Customer not found.")
        customer.is_deleted = True
        customer.deleted_at = _now()
        customer.deletion_reason = reason
        _record_history(business_id, customer.id, OrderHistoryEventType.CUSTOMER_DELETED, reason=reason)
        db.session.commit()

    @staticmethod
    def restore_customer(business_id: uuid.UUID, customer_id: uuid.UUID) -> OrderBookCustomer:
        customer = OrderBookCustomer.query.filter_by(id=customer_id, business_id=business_id, is_deleted=True).first()
        if customer is None:
            raise OrderBookNotFoundError("Customer not found in trash.")
        customer.is_deleted = False
        customer.deleted_at = None
        customer.deletion_reason = None
        _record_history(business_id, customer.id, OrderHistoryEventType.CUSTOMER_RESTORED)
        db.session.commit()
        return customer

    # --- Orders ----------------------------------------------------------

    @staticmethod
    def create_order(
        business_id: uuid.UUID,
        items: List[OrderLineItemInput],
        customer_id: Optional[uuid.UUID] = None,
        new_customer_name: Optional[str] = None,
        new_customer_phone: Optional[str] = None,
        notes: Optional[str] = None,
        order_id: Optional[uuid.UUID] = None,
    ) -> Order:
        if not items:
            raise OrderBookValidationError("Add at least one item.", field="items")

        customer = OrderBookService._resolve_or_create_customer(
            business_id, customer_id, new_customer_name, new_customer_phone
        )

        line_items: List[OrderLineItem] = []
        for item in items:
            if item.quantity <= 0:
                raise OrderBookValidationError("Quantity must be at least 1.", field="items")
            if item.unit_price.is_negative:
                raise OrderBookValidationError("Price can't be negative.", field="items")
            line_total = multiply(item.unit_price, item.quantity)
            line_items.append(OrderLineItem(
                id=uuid.uuid4(),
                description=item.description.strip(),
                quantity=item.quantity,
                unit_price_cents=item.unit_price.minor_units,
                line_total_cents=line_total.minor_units,
            ))

        order_total = total([Money(li.line_total_cents) for li in line_items])
        order_date = _today()
        next_number = OrderRepository.highest_order_number_for_date(business_id, order_date) + 1

        now = _now()
        order = Order(
            id=order_id or uuid.uuid4(),
            business_id=business_id,
            customer_id=customer.id,
            order_date=order_date,
            order_number=next_number,
            status=OrderStatus.PENDING,
            total_cents=order_total.minor_units,
            notes=notes.strip() if notes else None,
        )
        OrderRepository.create(order)

        for li in line_items:
            li.order_id = order.id
        LineItemRepository.create_all(line_items)

        _record_history(
            business_id, customer.id, OrderHistoryEventType.ORDER_CREATED,
            order_id=order.id, amount=order_total,
        )

        customer.last_transaction_at = now
        db.session.commit()
        return order

    @staticmethod
    def get_order(business_id: uuid.UUID, order_id: uuid.UUID) -> OrderView:
        order = OrderRepository.get_by_id(order_id, business_id)
        if order is None:
            raise OrderBookNotFoundError("Order not found.")
        return _to_view_or_raise(order)

    @staticmethod
    def list_orders(
        business_id: uuid.UUID,
        status: Optional[OrderStatus] = None,
        search_term: Optional[str] = None,
    ) -> List[OrderView]:
        orders = OrderRepository.list_for_business(business_id, status=status)
        if search_term and search_term.strip():
            term = search_term.strip().lower()
            customer_ids = {o.customer_id for o in orders}
            customers = {c.id: c for c in OrderBookCustomer.query.filter(OrderBookCustomer.id.in_(customer_ids)).all()} if customer_ids else {}
            orders = [
                o for o in orders
                if term in (customers.get(o.customer_id).name.lower() if customers.get(o.customer_id) else "")
                or term in (customers.get(o.customer_id).phone or "" if customers.get(o.customer_id) else "")
                or term in str(o.order_number)
            ]
        return _to_views(orders)

    @staticmethod
    def complete_order(business_id: uuid.UUID, order_id: uuid.UUID) -> OrderView:
        order = OrderRepository.get_by_id(order_id, business_id)
        if order is None:
            raise OrderBookNotFoundError("Order not found.")
        if order.status != OrderStatus.PENDING:
            raise OrderBookInvalidTransitionError("Only pending orders can be completed.")
        order.status = OrderStatus.COMPLETED
        order.completed_at = _now()
        _record_history(
            business_id, order.customer_id, OrderHistoryEventType.ORDER_COMPLETED,
            order_id=order.id, amount=Money(order.total_cents),
        )
        db.session.commit()
        return _to_view_or_raise(order)

    @staticmethod
    def cancel_order(business_id: uuid.UUID, order_id: uuid.UUID, reason: Optional[str] = None) -> OrderView:
        order = OrderRepository.get_by_id(order_id, business_id)
        if order is None:
            raise OrderBookNotFoundError("Order not found.")
        if order.status != OrderStatus.PENDING:
            raise OrderBookInvalidTransitionError("Only pending orders can be cancelled.")
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = _now()
        order.cancellation_reason = reason.strip() if reason else None
        _record_history(
            business_id, order.customer_id, OrderHistoryEventType.ORDER_CANCELLED,
            order_id=order.id, amount=Money(order.total_cents), reason=reason,
        )
        db.session.commit()
        return _to_view_or_raise(order)

    # --- Trash / soft-delete lifecycle -----------------------------------

    @staticmethod
    def delete_order(
        business_id: uuid.UUID,
        order_id: uuid.UUID,
        reason: Optional[str] = None,
        cause: OrderDeletionReason = OrderDeletionReason.MANUAL_DELETE,
    ) -> None:
        """Any status can be deleted (unlike complete/cancel, which
        only apply to PENDING orders) -- matches the frontend's
        'Delete order' action being available regardless of status."""
        order = OrderRepository.get_by_id(order_id, business_id)
        if order is None:
            raise OrderBookNotFoundError("Order not found.")
        order.is_deleted = True
        order.deleted_at = _now()
        order.deletion_reason = reason
        order.deletion_cause = cause
        _record_history(
            business_id, order.customer_id, OrderHistoryEventType.ORDER_DELETED,
            order_id=order.id, reason=reason,
        )
        db.session.commit()

    @staticmethod
    def restore_order(business_id: uuid.UUID, order_id: uuid.UUID) -> OrderView:
        order = Order.query.filter_by(id=order_id, business_id=business_id, is_deleted=True).first()
        if order is None:
            raise OrderBookNotFoundError("Order not found in trash.")
        order.is_deleted = False
        order.deleted_at = None
        order.deletion_reason = None
        order.deletion_cause = None
        _record_history(business_id, order.customer_id, OrderHistoryEventType.ORDER_RESTORED, order_id=order.id)
        db.session.commit()
        return _to_view_or_raise(order)

    @staticmethod
    def get_trash(business_id: uuid.UUID) -> dict:
        deleted_orders = OrderRepository.list_deleted_for_business(business_id)
        deleted_customers = CustomerRepository.list_deleted_for_business(business_id)

        customer_ids = {o.customer_id for o in deleted_orders}
        customers_by_id = {c.id: c for c in OrderBookCustomer.query.filter(OrderBookCustomer.id.in_(customer_ids)).all()} if customer_ids else {}

        all_items = LineItemRepository.list_for_orders([o.id for o in deleted_orders])
        items_by_order: Dict[uuid.UUID, List[OrderLineItem]] = {}
        for item in all_items:
            items_by_order.setdefault(item.order_id, []).append(item)

        order_entries = []
        for order in deleted_orders:
            customer = customers_by_id.get(order.customer_id)
            if customer is None:
                continue  # customer no longer resolvable (shouldn't happen; defensive)
            order_entries.append({
                "order": order,
                "customer": customer,
                "line_items": items_by_order.get(order.id, []),
                "days_remaining": days_remaining_in_trash(order.deleted_at),
            })

        customer_entries = [
            {"customer": c, "days_remaining": days_remaining_in_trash(c.deleted_at)}
            for c in deleted_customers
        ]

        return {"orders": order_entries, "customers": customer_entries}

    @staticmethod
    def clear_all_completed_now(business_id: uuid.UUID) -> int:
        """Manual 'Clear all completed' -- moves every active completed
        order to Trash right now, independent of the auto-clear
        setting. Returns the count cleared."""
        completed = OrderRepository.list_for_business(business_id, status=OrderStatus.COMPLETED)
        now = _now()
        for order in completed:
            order.is_deleted = True
            order.deleted_at = now
            order.deletion_cause = OrderDeletionReason.MANUAL_CLEAR_COMPLETED
        db.session.commit()
        return len(completed)

    # --- History -----------------------------------------------------------

    @staticmethod
    def get_history(business_id: uuid.UUID) -> List[OrderHistoryEvent]:
        return HistoryRepository.list_for_business(business_id)

    # --- Balances: daily revenue -------------------------------------------

    @staticmethod
    def get_daily_revenue(business_id: uuid.UUID) -> List[dict]:
        """Groups COMPLETED, non-deleted orders by the calendar date
        they were completed on. Mirrors the frontend's
        algorithms/dailyRevenue.ts calculateDailyRevenue exactly --
        cancelled/pending orders never contribute, and a cleared
        (trashed) completed order's money still happened but is
        excluded here just like the frontend excludes it, since Trash
        is reserved for its own screen."""
        completed = OrderRepository.list_for_business(business_id, status=OrderStatus.COMPLETED)
        by_date: Dict[date, dict] = {}
        for order in completed:
            if order.completed_at is None:
                continue
            key = order.completed_at.date()
            entry = by_date.setdefault(key, {"date": key, "total_cents": 0, "order_count": 0})
            entry["total_cents"] += order.total_cents
            entry["order_count"] += 1
        return sorted(by_date.values(), key=lambda e: e["date"], reverse=True)
