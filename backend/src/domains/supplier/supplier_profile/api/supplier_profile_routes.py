"""
supplier_profile HTTP routes -- the first real ones this domain has
ever had (see supplier_profile_service.py's own docstring: everything
before this was mock-only on the frontend).

DELIBERATELY DOES NOT REUSE products_routes.py's own
_supplier_profile_id() helper -- that one assumes a profile already
exists (raising 404 if not), which is the right assumption for a
supplier managing PRODUCTS (they can't have products without a
profile already existing). It's the WRONG assumption here: a
brand-new supplier calling GET /my-profile for the very first time,
before ever touching anything else, must still get a real (auto-
created) profile back, not a 404. The service layer's own
get_or_create_for_supplier already handles this -- these routes just
pass the raw user id through and let it.

AUTH: @fully_authenticated + @role_required("supplier") on every
route, same reasoning as every other supplier-only domain in this
codebase.
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import error_response, success_response
from src.domains.supplier.supplier_profile.schemas.supplier_profile_schemas import UpdateSupplierProfileSchema
from src.domains.supplier.supplier_profile.services import supplier_profile_service

supplier_profile_bp = Blueprint("supplier_profile", __name__)


def _flatten_marshmallow_errors(exc: MarshmallowValidationError) -> list[str]:
    """Same flatten-to-list-of-strings convention every other schema in
    this codebase uses (see products_routes.py's own copy)."""
    return [
        str(msg)
        for field_errors in exc.messages.values()
        for msg in (field_errors if isinstance(field_errors, list) else [field_errors])
    ]


def _to_dto(profile) -> dict:
    return {
        "businessName": profile.business_name,
        "category": profile.category,
        "location": profile.location,
        "description": profile.description,
        "photoVisibility": profile.photo_visibility.value,
        "visibleImageSource": profile.visible_image_source.value,
        "whatsappNumber": profile.whatsapp_number,
        "contactEmail": profile.contact_email,
        "tiktokHandle": profile.tiktok_handle,
        "shareContactDetails": profile.share_contact_details,
    }


@supplier_profile_bp.route("/api/v1/supplier-discovery/my-profile", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_my_profile():
    profile = supplier_profile_service.get_my_profile(get_jwt_identity())
    return success_response(data=_to_dto(profile))


@supplier_profile_bp.route("/api/v1/supplier-discovery/my-profile", methods=["PATCH"])
@fully_authenticated
@role_required("supplier")
def update_my_profile():
    payload = request.get_json(silent=True) or {}
    try:
        data = UpdateSupplierProfileSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    # ProfileValidationError isn't caught here -- same as every other
    # domain in this codebase, a global error handler already converts
    # it to a real 422 (see products_routes.py's own create_product for
    # the identical, already-proven pattern).
    profile = supplier_profile_service.update_my_profile(get_jwt_identity(), **data)
    return success_response(data=_to_dto(profile))
