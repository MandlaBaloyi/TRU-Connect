"""
SupplierOffer media routes -- the two supplier-facing endpoints
(request_media_upload_signature, register_media). The webhook itself
lives in shared/media/api/webhook_routes.py, not here, since it's not
supplier-scoped at all.

tier IS RESOLVED INSIDE THE SERVICE, NOT PASSED FROM HERE -- see
tiers/resolver.py's own docstring. Still honestly returns FREE for
every account today (no real Subscription domain exists yet), but the
route itself no longer needs to know that -- it just calls the
service, which asks the resolver.
"""
from __future__ import annotations

from flask import Blueprint, request
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import error_response, success_response
from src.domains.security.rate_limit.limiter import limiter
from src.domains.supplier.products.rate_limit import policies as rate_limit_policies
from src.domains.supplier.products.schemas.product_schemas import RegisterMediaSchema
from src.domains.supplier.products.services import product_media_service
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import SupplierProfileRepository

product_media_bp = Blueprint("product_media", __name__)


def _supplier_profile_id():
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


@product_media_bp.route("/api/v1/supplier-discovery/products/<product_id>/media/upload-signature", methods=["POST"])
@fully_authenticated
@role_required("supplier")
@limiter.limit(rate_limit_policies.MEDIA_SIGN, key_func=rate_limit_policies.supplier_key_func)
def request_media_upload_signature(product_id: str):
    signed = product_media_service.request_upload_signature(product_id, _supplier_profile_id())
    return success_response(
        data={
            "cloud_name": signed.cloud_name,
            "api_key": signed.api_key,
            "timestamp": signed.timestamp,
            "signature": signed.signature,
            "public_id": signed.public_id,
            "upload_url": signed.upload_url,
            "allowed_formats": signed.allowed_formats,
            "transformation": signed.transformation,
            "notification_url": signed.notification_url,
            "moderation": signed.moderation,
            "asset_folder": signed.asset_folder,
        }
    )


@product_media_bp.route("/api/v1/supplier-discovery/products/<product_id>/media", methods=["POST"])
@fully_authenticated
@role_required("supplier")
def register_media(product_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = RegisterMediaSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    media = product_media_service.register_uploaded_media(
        product_id=product_id,
        supplier_profile_id=_supplier_profile_id(),
        cloudinary_public_id=data["cloudinary_public_id"],
        secure_url=data["secure_url"],
        resource_type=data["resource_type"],
        format=data["format"],
        width=data["width"],
        height=data["height"],
        bytes_=data["bytes"],
    )
    return success_response(
        data={
            "id": str(media.id),
            "product_id": str(media.product_id),
            "secure_url": media.secure_url,
            "scan_status": media.scan_status,
            "sort_order": media.sort_order,
        },
        status_code=201,
    )
