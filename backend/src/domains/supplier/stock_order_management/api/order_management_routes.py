"""
domains.supplier.stock_order_management HTTP routes -- the supplier's
own real actions on an order: view what's pending, approve, decline,
and browse their own real history by status and date range.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from flask import Blueprint, request

from src.core.decorators import fully_authenticated, role_required
from src.core.exceptions import ValidationError
from src.core.responses import success_response
from src.domains.supplier.stock_order_management.services import order_management_service
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)

order_management_bp = Blueprint("order_management", __name__)


def _supplier_profile_id() -> uuid.UUID:
    from flask_jwt_extended import get_jwt_identity
    from src.core.exceptions import NotFoundError

    user_id = get_jwt_identity()
    profile = SupplierProfileRepository.get_by_supplier_id(user_id)
    if not profile:
        raise NotFoundError("Supplier profile not found.", code="SUPPLIER_PROFILE_NOT_FOUND")
    return profile.id


def _parse_iso_datetime(raw: str | None, param_name: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        raise ValidationError(f"'{param_name}' must be a real ISO-8601 date/time.")


@order_management_bp.route("/api/v1/supplier/stock-orders", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def list_orders():
    """No ?status= -> the real, unchanged "New" queue (pending only,
    exactly as before). ?status=CONFIRMED or ?status=DECLINED -> the
    Approved/Declined tabs' own real history, optionally narrowed by
    ?from=/&to= (real ISO-8601 timestamps)."""
    status = request.args.get("status")
    if not status:
        results = order_management_service.list_pending_orders(_supplier_profile_id())
        return success_response(data={"orders": results})

    submitted_from = _parse_iso_datetime(request.args.get("from"), "from")
    submitted_to = _parse_iso_datetime(request.args.get("to"), "to")
    results = order_management_service.list_orders_by_status(
        _supplier_profile_id(), status, submitted_from, submitted_to
    )
    return success_response(data={"orders": results})


@order_management_bp.route("/api/v1/supplier/stock-orders/<uuid:order_id>", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_order_detail(order_id: uuid.UUID):
    result = order_management_service.get_order_detail(_supplier_profile_id(), order_id)
    return success_response(data=result)


@order_management_bp.route("/api/v1/supplier/stock-orders/<uuid:order_id>/approve", methods=["POST"])
@fully_authenticated
@role_required("supplier")
def approve_order(order_id: uuid.UUID):
    result = order_management_service.approve_order(_supplier_profile_id(), order_id)
    return success_response(data=result)


@order_management_bp.route("/api/v1/supplier/stock-orders/<uuid:order_id>/decline", methods=["POST"])
@fully_authenticated
@role_required("supplier")
def decline_order(order_id: uuid.UUID):
    body = request.get_json(silent=True) or {}
    result = order_management_service.decline_order(
        _supplier_profile_id(), order_id, reason=body.get("reason"), details=body.get("details")
    )
    return success_response(data=result)


@order_management_bp.route("/api/v1/supplier/stock-orders/<uuid:order_id>/cancel", methods=["POST"])
@fully_authenticated
@role_required("supplier")
def cancel_order(order_id: uuid.UUID):
    """CONFIRMED -> CANCELLED only -- see order_management_service.
    cancel_order's own docstring for why this is a genuinely different
    door from decline above, not the same action with a different
    name."""
    body = request.get_json(silent=True) or {}
    result = order_management_service.cancel_order(
        _supplier_profile_id(), order_id, reason=body.get("reason"), details=body.get("details")
    )
    return success_response(data=result)
