"""
Order Book HTTP routes.

AUTH DECORATOR: `fully_authenticated` from `src.core.decorators` --
VERIFIED at this exact import path (confirmed by directly reading
src/core/decorators.py in this same session, not guessed by pattern
like Loan Book's routes file had to flag).

business_id is taken from get_jwt_identity() -- the authenticated
caller's own user id -- NEVER from anything in the request body or
URL. Same non-negotiable mechanism as loan_book_routes.py; see that
file's docstring for why a route reading business_id from a request
parameter would make every downstream ownership check pointless.
"""
from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated
from src.domains.business.order_book.models.auto_clear_settings import AutoClearDuration
from src.domains.business.order_book.models.order import OrderDeletionReason, OrderStatus
from src.domains.business.order_book.schemas.order_book_schemas import (
    CancelOrderSchema,
    CreateOrderSchema,
    DeleteReasonSchema,
    SetAutoClearSettingSchema,
)
from src.domains.business.order_book.services.auto_clear_service import AutoClearService
from src.domains.business.order_book.services.errors import (
    OrderBookInvalidTransitionError,
    OrderBookNotFoundError,
    OrderBookValidationError,
)
from src.domains.business.order_book.services.order_book_service import OrderBookService, OrderLineItemInput
from src.shared.finance import Money, format_for_json

order_book_bp = Blueprint("order_book", __name__)


def _business_id() -> uuid.UUID:
    return uuid.UUID(get_jwt_identity())


# --- Serialization ---------------------------------------------------------

def _line_item_to_dict(item) -> dict:
    return {
        "id": str(item.id),
        "description": item.description,
        "quantity": item.quantity,
        "unitPrice": format_for_json(Money(item.unit_price_cents)),
        "lineTotal": format_for_json(Money(item.line_total_cents)),
    }


def _order_to_dict(order) -> dict:
    return {
        "id": str(order.id),
        "customerId": str(order.customer_id),
        "orderDate": order.order_date.isoformat(),
        "orderNumber": order.order_number,
        "status": order.status.value,
        "total": format_for_json(Money(order.total_cents)),
        "notes": order.notes,
        "createdAt": order.created_at.isoformat(),
        "updatedAt": order.updated_at.isoformat(),
        "completedAt": order.completed_at.isoformat() if order.completed_at else None,
        "cancelledAt": order.cancelled_at.isoformat() if order.cancelled_at else None,
        "cancellationReason": order.cancellation_reason,
    }


def _order_view_to_dict(view) -> dict:
    return {
        **_order_to_dict(view.order),
        "customer": _customer_to_dict(view.customer),
        "lineItems": [_line_item_to_dict(i) for i in view.line_items],
    }


def _customer_to_dict(customer) -> dict:
    return {
        "id": str(customer.id),
        "name": customer.name,
        "phone": customer.phone,
    }


def _history_event_to_dict(event) -> dict:
    return {
        "id": str(event.id),
        "customerId": str(event.customer_id),
        "orderId": str(event.order_id) if event.order_id else None,
        "eventType": event.event_type.value,
        "amount": format_for_json(Money(event.amount_cents)) if event.amount_cents is not None else None,
        "reason": event.reason,
        "occurredAt": event.occurred_at.isoformat(),
    }


def _auto_clear_settings_to_dict(settings) -> dict:
    return {
        "completed": {
            "duration": settings.completed_duration.value.upper(),
            "customHours": settings.completed_custom_hours,
        },
        "cancelled": {
            "duration": settings.cancelled_duration.value.upper(),
            "customHours": settings.cancelled_custom_hours,
        },
    }


# --- Orders ------------------------------------------------------------

@order_book_bp.route("/api/v1/order-book/orders", methods=["POST"])
@fully_authenticated
def create_order():
    try:
        data = CreateOrderSchema().load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as exc:
        return jsonify(success=False, errors=exc.messages), 422

    items = [
        OrderLineItemInput(
            description=item["description"],
            quantity=item["quantity"],
            unit_price=Money(item["unit_price_cents"]),
        )
        for item in data["items"]
    ]

    try:
        order = OrderBookService.create_order(
            _business_id(),
            items,
            customer_id=data.get("customer_id"),
            new_customer_name=data.get("new_customer_name"),
            new_customer_phone=data.get("new_customer_phone"),
            notes=data.get("notes"),
            order_id=data.get("id"),
        )
    except OrderBookNotFoundError:
        return jsonify(success=False, message="Customer not found."), 404
    except OrderBookValidationError as exc:
        return jsonify(success=False, message=exc.message, field=exc.field), 422

    view = OrderBookService.get_order(_business_id(), order.id)
    return jsonify(success=True, data=_order_view_to_dict(view)), 201


@order_book_bp.route("/api/v1/order-book/orders", methods=["GET"])
@fully_authenticated
def list_orders():
    status_param = request.args.get("status")
    status = None
    if status_param:
        try:
            status = OrderStatus(status_param.lower())
        except ValueError:
            return jsonify(success=False, message="Invalid status filter."), 422

    search_term = request.args.get("search")
    views = OrderBookService.list_orders(_business_id(), status=status, search_term=search_term)
    return jsonify(success=True, data=[_order_view_to_dict(v) for v in views])


@order_book_bp.route("/api/v1/order-book/orders/<uuid:order_id>", methods=["GET"])
@fully_authenticated
def get_order(order_id: uuid.UUID):
    try:
        view = OrderBookService.get_order(_business_id(), order_id)
    except OrderBookNotFoundError:
        return jsonify(success=False, message="Order not found."), 404
    return jsonify(success=True, data=_order_view_to_dict(view))


@order_book_bp.route("/api/v1/order-book/orders/<uuid:order_id>/complete", methods=["POST"])
@fully_authenticated
def complete_order(order_id: uuid.UUID):
    try:
        view = OrderBookService.complete_order(_business_id(), order_id)
    except OrderBookNotFoundError:
        return jsonify(success=False, message="Order not found."), 404
    except OrderBookInvalidTransitionError as exc:
        return jsonify(success=False, message=exc.message), 409
    return jsonify(success=True, data=_order_view_to_dict(view))


@order_book_bp.route("/api/v1/order-book/orders/<uuid:order_id>/cancel", methods=["POST"])
@fully_authenticated
def cancel_order(order_id: uuid.UUID):
    data = CancelOrderSchema().load(request.get_json(silent=True) or {})
    try:
        view = OrderBookService.cancel_order(_business_id(), order_id, reason=data.get("reason"))
    except OrderBookNotFoundError:
        return jsonify(success=False, message="Order not found."), 404
    except OrderBookInvalidTransitionError as exc:
        return jsonify(success=False, message=exc.message), 409
    return jsonify(success=True, data=_order_view_to_dict(view))


@order_book_bp.route("/api/v1/order-book/orders/<uuid:order_id>", methods=["DELETE"])
@fully_authenticated
def delete_order(order_id: uuid.UUID):
    data = DeleteReasonSchema().load(request.get_json(silent=True) or {})
    try:
        OrderBookService.delete_order(
            _business_id(), order_id, reason=data.get("reason"), cause=OrderDeletionReason.MANUAL_DELETE
        )
    except OrderBookNotFoundError:
        return jsonify(success=False, message="Order not found."), 404
    return jsonify(success=True), 200


@order_book_bp.route("/api/v1/order-book/orders/<uuid:order_id>/restore", methods=["POST"])
@fully_authenticated
def restore_order(order_id: uuid.UUID):
    try:
        view = OrderBookService.restore_order(_business_id(), order_id)
    except OrderBookNotFoundError:
        return jsonify(success=False, message="Order not found in trash."), 404
    return jsonify(success=True, data=_order_view_to_dict(view))


@order_book_bp.route("/api/v1/order-book/orders/clear-completed", methods=["POST"])
@fully_authenticated
def clear_completed_orders():
    cleared_count = OrderBookService.clear_all_completed_now(_business_id())
    return jsonify(success=True, data={"clearedCount": cleared_count})


# --- Customers (Order Book's own — see order_book_service.py) -----

@order_book_bp.route("/api/v1/order-book/customers/search", methods=["GET"])
@fully_authenticated
def search_customers():
    term = request.args.get("term", "")
    customers = OrderBookService.search_customers(_business_id(), term)
    return jsonify(success=True, data=[_customer_to_dict(c) for c in customers])


@order_book_bp.route("/api/v1/order-book/customers/<uuid:customer_id>", methods=["DELETE"])
@fully_authenticated
def delete_customer(customer_id: uuid.UUID):
    data = DeleteReasonSchema().load(request.get_json(silent=True) or {})
    try:
        OrderBookService.delete_customer(_business_id(), customer_id, reason=data.get("reason"))
    except OrderBookNotFoundError:
        return jsonify(success=False, message="Customer not found."), 404
    return jsonify(success=True), 200


@order_book_bp.route("/api/v1/order-book/customers/<uuid:customer_id>/restore", methods=["POST"])
@fully_authenticated
def restore_customer(customer_id: uuid.UUID):
    try:
        customer = OrderBookService.restore_customer(_business_id(), customer_id)
    except OrderBookNotFoundError:
        return jsonify(success=False, message="Customer not found in trash."), 404
    return jsonify(success=True, data=_customer_to_dict(customer))


# --- Trash ---------------------------------------------------------------

@order_book_bp.route("/api/v1/order-book/trash", methods=["GET"])
@fully_authenticated
def get_trash():
    trash = OrderBookService.get_trash(_business_id())
    return jsonify(
        success=True,
        data={
            "orders": [
                {
                    **_order_to_dict(e["order"]),
                    "customer": _customer_to_dict(e["customer"]),
                    "lineItems": [_line_item_to_dict(i) for i in e["line_items"]],
                    "daysRemaining": e["days_remaining"],
                }
                for e in trash["orders"]
            ],
            "customers": [
                {**_customer_to_dict(e["customer"]), "daysRemaining": e["days_remaining"]}
                for e in trash["customers"]
            ],
        },
    )


# --- History ---------------------------------------------------------------

@order_book_bp.route("/api/v1/order-book/history", methods=["GET"])
@fully_authenticated
def get_history():
    events = OrderBookService.get_history(_business_id())
    return jsonify(success=True, data=[_history_event_to_dict(e) for e in events])


# --- Balances --------------------------------------------------------------

@order_book_bp.route("/api/v1/order-book/balances/daily-revenue", methods=["GET"])
@fully_authenticated
def get_daily_revenue():
    entries = OrderBookService.get_daily_revenue(_business_id())
    return jsonify(
        success=True,
        data=[
            {"date": e["date"].isoformat(), "totalCents": e["total_cents"], "orderCount": e["order_count"]}
            for e in entries
        ],
    )


@order_book_bp.route("/api/v1/order-book/balances/auto-clear-settings", methods=["GET"])
@fully_authenticated
def get_auto_clear_settings():
    settings = AutoClearService.get_settings(_business_id())
    return jsonify(success=True, data=_auto_clear_settings_to_dict(settings))


@order_book_bp.route("/api/v1/order-book/balances/auto-clear-settings", methods=["PUT"])
@fully_authenticated
def set_auto_clear_setting():
    try:
        data = SetAutoClearSettingSchema().load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as exc:
        return jsonify(success=False, errors=exc.messages), 422

    duration_map = {
        "OFF": AutoClearDuration.OFF,
        "5_MIN": AutoClearDuration.FIVE_MIN,
        "15_MIN": AutoClearDuration.FIFTEEN_MIN,
        "CUSTOM": AutoClearDuration.CUSTOM,
    }
    try:
        settings = AutoClearService.set_setting(
            _business_id(), data["scope"], duration_map[data["duration"]], data.get("custom_hours"),
        )
    except OrderBookValidationError as exc:
        return jsonify(success=False, message=exc.message, field=exc.field), 422
    return jsonify(success=True, data=_auto_clear_settings_to_dict(settings))


@order_book_bp.route("/api/v1/order-book/balances/auto-clear-sweep", methods=["POST"])
@fully_authenticated
def run_auto_clear_sweep():
    """Manual trigger, scoped to the caller's own business only. A real
    scheduled job also exists now (jobs/auto_clear_sweep_job.py, every
    60s, all eligible businesses) — this route is a supplement to that,
    not a replacement: useful for "I don't want to wait up to a
    minute" testing/manual use, not the only thing keeping Trash
    current."""
    cleared_count = AutoClearService.run_sweep(_business_id())
    return jsonify(success=True, data={"clearedCount": cleared_count})
