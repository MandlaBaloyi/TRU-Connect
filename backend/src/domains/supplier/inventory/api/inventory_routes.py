"""
Inventory HTTP routes. URL prefix /api/v1/supplier-discovery/inventory
-- matching frontend/src/features/dashboard/supplier/inventory/api/
httpInventoryApi.ts exactly, same "URL namespace is inherited from
Find Supplier, backend domain folder name is independent" reasoning as
products_routes.py's own docstring.

DTO FIELD NAME NOTE: the inventory sub-object's owner field is
`supplier_id` in the JSON response (not `supplier_profile_id`) --
matching the frontend's own ApiInventoryListItem.inventory.supplier_id
exactly, even though every other DTO in this backend calls the same
concept supplier_profile_id. The frontend contract was locked before
this backend existed; matching it exactly here is correct, not an
inconsistency to "fix".
"""
from __future__ import annotations

import uuid

from flask import Blueprint, request
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import error_response, success_response
from src.domains.security.rate_limit.limiter import limiter
from src.domains.supplier.inventory.rate_limit import policies as rate_limit_policies
from src.domains.supplier.inventory.schemas.inventory_schemas import (
    AdjustStockSchema,
    SetThresholdSchema,
    UpdateSettingsSchema,
)
from src.domains.supplier.inventory.services import inventory_service
from src.domains.supplier.products.services import product_media_service
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import SupplierProfileRepository

inventory_bp = Blueprint("inventory", __name__)


def _supplier_profile_id() -> uuid.UUID:
    from flask_jwt_extended import get_jwt_identity
    from src.core.exceptions import NotFoundError

    user_id = get_jwt_identity()
    profile = SupplierProfileRepository.get_by_supplier_id(user_id)
    if not profile:
        raise NotFoundError("Supplier profile not found.", code="SUPPLIER_PROFILE_NOT_FOUND")
    return profile.id


def _flatten_marshmallow_errors(exc: MarshmallowValidationError) -> list[str]:
    return [
        str(msg)
        for field_errors in exc.messages.values()
        for msg in (field_errors if isinstance(field_errors, list) else [field_errors])
    ]


def _to_dto(item: dict) -> dict:
    product = item["product"]
    inventory = item["inventory"]
    return {
        "product": {
            "id": str(product.id),
            "name": product.name,
            "category": product.category.value,
            "price_cents": product.price_cents,
            "selling_unit": product.selling_unit.value,
            "images": product_media_service.list_approved_media(product.id),
            "is_archived": product.is_archived,
        },
        "inventory": {
            "id": str(inventory.id),
            "product_id": str(inventory.product_id),
            "supplier_id": str(inventory.supplier_profile_id),
            "quantity_on_hand": inventory.quantity_on_hand,
            "quantity_reserved": inventory.quantity_reserved,
            "low_stock_threshold": inventory.low_stock_threshold,
            "created_at": inventory.created_at.isoformat(),
            "updated_at": inventory.updated_at.isoformat(),
        },
        "status": item["status"],
        "available_quantity": item["available_quantity"],
    }


def _settings_to_dto(settings) -> dict:
    return {
        "default_low_stock_threshold": settings.default_low_stock_threshold,
        "low_stock_alert_channel": settings.low_stock_alert_channel.value,
    }


@inventory_bp.route("/api/v1/supplier-discovery/inventory", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def list_inventory():
    status_filter = request.args.get("filter") or None
    search_term = request.args.get("q") or None
    items = inventory_service.get_inventory_list(
        _supplier_profile_id(), status_filter=status_filter, search_term=search_term
    )
    return success_response(data={"results": [_to_dto(item) for item in items]})


@inventory_bp.route("/api/v1/supplier-discovery/inventory/summary", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_summary():
    summary = inventory_service.get_inventory_summary(_supplier_profile_id())
    return success_response(data=summary)


@inventory_bp.route("/api/v1/supplier-discovery/inventory/settings", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_settings():
    settings = inventory_service.get_settings(_supplier_profile_id())
    return success_response(data=_settings_to_dto(settings))


@inventory_bp.route("/api/v1/supplier-discovery/inventory/settings", methods=["PUT"])
@fully_authenticated
@role_required("supplier")
def update_settings():
    payload = request.get_json(silent=True) or {}
    try:
        data = UpdateSettingsSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    settings = inventory_service.update_settings(
        _supplier_profile_id(),
        default_low_stock_threshold=data.get("default_low_stock_threshold"),
        low_stock_alert_channel=data.get("low_stock_alert_channel"),
    )
    return success_response(data=_settings_to_dto(settings))


@inventory_bp.route("/api/v1/supplier-discovery/inventory/<product_id>", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_inventory_item(product_id: str):
    item = inventory_service.get_inventory_item(product_id, _supplier_profile_id())
    return success_response(data=_to_dto(item))


@inventory_bp.route("/api/v1/supplier-discovery/inventory/<product_id>/adjust", methods=["POST"])
@fully_authenticated
@role_required("supplier")
@limiter.limit(rate_limit_policies.INVENTORY_ADJUST, key_func=rate_limit_policies.supplier_key_func)
def adjust_stock(product_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = AdjustStockSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    item = inventory_service.adjust_stock(
        product_id, _supplier_profile_id(), data["quantity_delta"], data["reason"]
    )
    return success_response(data=_to_dto(item))


@inventory_bp.route("/api/v1/supplier-discovery/inventory/<product_id>/threshold", methods=["PUT"])
@fully_authenticated
@role_required("supplier")
def set_threshold(product_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = SetThresholdSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    item = inventory_service.set_low_stock_threshold(
        product_id, _supplier_profile_id(), data["low_stock_threshold"]
    )
    return success_response(data=_to_dto(item))
