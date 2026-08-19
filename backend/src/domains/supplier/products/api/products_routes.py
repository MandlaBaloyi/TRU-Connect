"""
Products HTTP routes.

URL PREFIX IS /api/v1/supplier-discovery/products, NOT /api/v1/products
-- deliberate, matching the frontend's own httpProductsApi.ts, which
was written before this backend existed and already hardcodes that
exact path. The URL namespace ("supplier-discovery", inherited from
Find Supplier/connections' own naming) and this backend domain folder
name ("products") are allowed to differ -- renaming the domain folder
per review didn't require renaming the URL a frontend already depends
on, and breaking a locked contract to satisfy an internal folder name
would be exactly backwards.

AUTH: @fully_authenticated + @role_required("supplier") on every
route, same reasoning connections_routes.py's own docstring gives for
why role_required matters once both roles are real, valid JWT
holders.

supplier_profile_id is resolved from the JWT identity via
SupplierProfileRepository, NEVER taken from the request body or URL --
same rule every other route in this codebase follows (see
connections_routes.py's own docstring on business_id for the identical
reasoning applied to the other role).
"""
from __future__ import annotations

import uuid

from flask import Blueprint, request
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import error_response, success_response
from src.domains.security.rate_limit.limiter import limiter
from src.domains.supplier.products.rate_limit import policies as rate_limit_policies
from src.domains.supplier.products.schemas.product_schemas import (
    BulkAdjustPriceSchema,
    BulkArchiveSchema,
    CreateProductSchema,
    UpdateProductSchema,
)
from src.domains.supplier.products.services import product_media_service, product_service
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import SupplierProfileRepository

products_bp = Blueprint("products", __name__)


def _supplier_profile_id() -> uuid.UUID:
    from flask_jwt_extended import get_jwt_identity
    from src.core.exceptions import NotFoundError

    user_id = get_jwt_identity()
    profile = SupplierProfileRepository.get_by_supplier_id(user_id)
    if not profile:
        # Shouldn't normally happen -- get_or_create_for_supplier runs
        # at first OTP verification, and fully_authenticated already
        # requires a verified account. Defensive, not a real expected
        # path.
        raise NotFoundError("Supplier profile not found.", code="SUPPLIER_PROFILE_NOT_FOUND")
    return profile.id


def _flatten_marshmallow_errors(exc: MarshmallowValidationError) -> list[str]:
    """Same flatten-to-list-of-strings convention every other schema
    in this codebase uses (see connections_routes.py's own
    invite_supplier route) -- error_response's own `errors` field is a
    flat list, and the frontend's ApiError class already expects
    exactly that shape (errors: string[]), not field-keyed objects."""
    return [
        str(msg)
        for field_errors in exc.messages.values()
        for msg in (field_errors if isinstance(field_errors, list) else [field_errors])
    ]


def _to_dto(product) -> dict:
    return {
        "id": str(product.id),
        "supplier_profile_id": str(product.supplier_profile_id),
        "name": product.name,
        "category": product.category.value,
        "price_cents": product.price_cents,
        "selling_unit": product.selling_unit.value,
        "unit_quantity": product.unit_quantity,
        "unit_measure": product.unit_measure.value if product.unit_measure else None,
        # Real, APPROVED-only media -- see product_media_service's own
        # list_approved_media docstring. Never PENDING/REJECTED/ERROR;
        # those aren't this supplier's own screens' concern to filter,
        # the query itself never returns them.
        "images": product_media_service.list_approved_media(product.id),
        "is_archived": product.is_archived,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
    }


@products_bp.route("/api/v1/supplier-discovery/products", methods=["POST"])
@fully_authenticated
@role_required("supplier")
@limiter.limit(rate_limit_policies.PRODUCT_CREATE, key_func=rate_limit_policies.supplier_key_func)
def create_product():
    payload = request.get_json(silent=True) or {}
    try:
        data = CreateProductSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    product = product_service.create_product(
        supplier_profile_id=_supplier_profile_id(),
        name=data["name"],
        category=data["category"],
        price_cents=data["price_cents"],
        selling_unit=data["selling_unit"],
        unit_quantity=data.get("unit_quantity"),
        unit_measure=data.get("unit_measure"),
    )
    return success_response(data=_to_dto(product), status_code=201)


@products_bp.route("/api/v1/supplier-discovery/products", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def list_products():
    include_archived = request.args.get("filter") == "ARCHIVED"
    search_term = request.args.get("q") or None
    products = product_service.list_products(
        _supplier_profile_id(), include_archived=include_archived, search_term=search_term
    )
    return success_response(data={"results": [_to_dto(p) for p in products]})


@products_bp.route("/api/v1/supplier-discovery/products/<product_id>", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_product(product_id: str):
    product = product_service.get_product(product_id, _supplier_profile_id())
    return success_response(data=_to_dto(product))


@products_bp.route("/api/v1/supplier-discovery/products/<product_id>", methods=["PATCH"])
@fully_authenticated
@role_required("supplier")
def update_product(product_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = UpdateProductSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    product = product_service.update_product(
        product_id=product_id,
        supplier_profile_id=_supplier_profile_id(),
        name=data["name"],
        category=data["category"],
        price_cents=data["price_cents"],
        selling_unit=data["selling_unit"],
    )
    return success_response(data=_to_dto(product))


@products_bp.route("/api/v1/supplier-discovery/products/<product_id>/archive", methods=["POST"])
@fully_authenticated
@role_required("supplier")
def archive_product(product_id: str):
    product = product_service.archive_product(product_id, _supplier_profile_id())
    return success_response(data=_to_dto(product))


@products_bp.route("/api/v1/supplier-discovery/products/bulk/adjust-price", methods=["POST"])
@fully_authenticated
@role_required("supplier")
@limiter.limit(rate_limit_policies.PRODUCT_BULK_ACTION, key_func=rate_limit_policies.supplier_key_func)
def bulk_adjust_price():
    payload = request.get_json(silent=True) or {}
    try:
        data = BulkAdjustPriceSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    products = product_service.bulk_adjust_price(
        product_ids=data["product_ids"],
        supplier_profile_id=_supplier_profile_id(),
        direction=data["direction"],
        adjustment_type=data["type"],
        value=data["value"],
    )
    return success_response(data={"results": [_to_dto(p) for p in products]})


@products_bp.route("/api/v1/supplier-discovery/products/bulk/archive", methods=["POST"])
@fully_authenticated
@role_required("supplier")
@limiter.limit(rate_limit_policies.PRODUCT_BULK_ACTION, key_func=rate_limit_policies.supplier_key_func)
def bulk_archive():
    payload = request.get_json(silent=True) or {}
    try:
        data = BulkArchiveSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    products = product_service.bulk_archive(data["product_ids"], _supplier_profile_id())
    return success_response(data={"results": [_to_dto(p) for p in products]})
