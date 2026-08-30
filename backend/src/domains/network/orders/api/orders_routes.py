"""
domains/network/orders HTTP routes -- business-facing for this pass (a
supplier-side "incoming orders" feature is real, separate, later
work, per the agreed build order).

AUTH: @fully_authenticated + @role_required("business") on every
route, same discipline as connections_routes.py's own docstring on
why role_required matters here specifically -- a supplier account
building a "cart" against a supplier_profile_id would be a genuine
authorization bug, not just an unlikely accident.

business_id is taken from get_jwt_identity() ONLY -- never from the
request body or URL, same rule as every other route in this codebase.
"""
from __future__ import annotations

import uuid

from flask import Blueprint, request
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import error_response, success_response
from src.domains.network.orders.rate_limit import policies as rate_limit_policies
from src.domains.network.orders.schemas.checkout_schemas import AddCartItemSchema, SubmitCheckoutSchema, UpdateCartItemSchema
from src.domains.network.orders.services import cart_service, checkout_service, order_history_service
from src.domains.security.rate_limit.limiter import limiter

orders_bp = Blueprint("orders", __name__)


def _business_id() -> uuid.UUID:
    from flask_jwt_extended import get_jwt_identity

    return uuid.UUID(get_jwt_identity())


def _load_or_422(schema_cls, payload: dict):
    try:
        return schema_cls().load(payload), None
    except MarshmallowValidationError as exc:
        errors = [str(msg) for field_errors in exc.messages.values() for msg in field_errors]
        return None, error_response(message="Validation failed", errors=errors, status_code=422)


@orders_bp.route("/api/v1/checkout/suppliers/<uuid:supplier_profile_id>/items", methods=["POST"])
@fully_authenticated
@role_required("business")
def add_cart_item(supplier_profile_id: uuid.UUID):
    payload = request.get_json(silent=True) or {}
    data, error = _load_or_422(AddCartItemSchema, payload)
    if error:
        return error

    result = cart_service.add_item(_business_id(), supplier_profile_id, data["product_id"], data["quantity"])
    return success_response(data=result)


@orders_bp.route(
    "/api/v1/checkout/suppliers/<uuid:supplier_profile_id>/items/<uuid:product_id>", methods=["PATCH"]
)
@fully_authenticated
@role_required("business")
def update_cart_item(supplier_profile_id: uuid.UUID, product_id: uuid.UUID):
    payload = request.get_json(silent=True) or {}
    data, error = _load_or_422(UpdateCartItemSchema, payload)
    if error:
        return error

    result = cart_service.update_item_quantity(_business_id(), supplier_profile_id, product_id, data["quantity"])
    return success_response(data=result)


@orders_bp.route(
    "/api/v1/checkout/suppliers/<uuid:supplier_profile_id>/items/<uuid:product_id>", methods=["DELETE"]
)
@fully_authenticated
@role_required("business")
def remove_cart_item(supplier_profile_id: uuid.UUID, product_id: uuid.UUID):
    result = cart_service.remove_item(_business_id(), supplier_profile_id, product_id)
    return success_response(data=result)


@orders_bp.route("/api/v1/checkout/suppliers/<uuid:supplier_profile_id>/cart/clear", methods=["POST"])
@fully_authenticated
@role_required("business")
def clear_cart(supplier_profile_id: uuid.UUID):
    result = cart_service.clear_cart(_business_id(), supplier_profile_id)
    return success_response(data=result)


@orders_bp.route("/api/v1/checkout/suppliers/<uuid:supplier_profile_id>/cart", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_supplier_cart(supplier_profile_id: uuid.UUID):
    """null (not a 404) when no cart exists yet for this supplier --
    "you have nothing here" is a normal, expected state for the
    Stock Catalogue's own cart badge to check, not an error."""
    result = cart_service.get_cart(_business_id(), supplier_profile_id)
    return success_response(data=result)


@orders_bp.route("/api/v1/checkout/carts", methods=["GET"])
@fully_authenticated
@role_required("business")
def list_my_carts():
    """The Account tab's own "My Checkouts" hub -- every supplier this
    business currently has an incomplete cart with."""
    results = cart_service.list_my_carts(_business_id())
    return success_response(data={"carts": results})


@orders_bp.route("/api/v1/checkout/suppliers/<uuid:supplier_profile_id>/history", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_order_history(supplier_profile_id: uuid.UUID):
    """"Order History" -- reached from the Stock Catalogue's own
    3-dot menu, one supplier at a time."""
    results = order_history_service.list_order_history(_business_id(), supplier_profile_id)
    return success_response(data={"orders": results})


@orders_bp.route("/api/v1/checkout/suppliers/<uuid:supplier_profile_id>/submit", methods=["POST"])
@fully_authenticated
@role_required("business")
@limiter.limit(rate_limit_policies.SUBMIT_CHECKOUT, key_func=rate_limit_policies.business_key_func)
def submit_checkout(supplier_profile_id: uuid.UUID):
    payload = request.get_json(silent=True) or {}
    data, error = _load_or_422(SubmitCheckoutSchema, payload)
    if error:
        return error

    result = checkout_service.submit_checkout(
        _business_id(),
        supplier_profile_id,
        data["payment_method"],
        data["delivery_type"],
        data["delivery_address_text"],
    )
    return success_response(data=result)
