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
pass the raw user id through and let it. The image routes below go
through that same get-or-create path for the identical reason.

AUTH: @fully_authenticated + @role_required("supplier") on every
route, same reasoning as every other supplier-only domain in this
codebase.

IMAGE UPLOAD follows the exact signed-client-upload flow products
already uses (see products/api/media_routes.py): this backend signs an
upload, the client uploads the bytes DIRECTLY to Cloudinary, then
registers the result here. Flask never carries image bytes.
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import error_response, success_response
from src.domains.security.rate_limit.limiter import limiter
from src.domains.supplier.products.rate_limit import policies as products_rate_limit_policies
from src.domains.supplier.supplier_profile.schemas.supplier_profile_schemas import (
    ProfileImageSignatureSchema,
    RegisterProfileImageSchema,
    UpdateSupplierProfileSchema,
)
from src.domains.supplier.supplier_profile.services import (
    supplier_profile_image_service,
    supplier_profile_service,
)

supplier_profile_bp = Blueprint("supplier_profile", __name__)


def _supplier_profile_id():
    """Resolves (auto-creating if needed) the caller's own
    SupplierProfile id -- same get-or-create path as get_my_profile, so
    a brand-new supplier's first image upload works without a prior
    profile-setup step."""
    return supplier_profile_service.get_my_profile(get_jwt_identity()).id


def _flatten_marshmallow_errors(exc: MarshmallowValidationError) -> list[str]:
    """Same flatten-to-list-of-strings convention every other schema in
    this codebase uses (see products_routes.py's own copy)."""
    return [
        str(msg)
        for field_errors in exc.messages.values()
        for msg in (field_errors if isinstance(field_errors, list) else [field_errors])
    ]


def _performance_stats(profile) -> dict:
    """This supplier's own acceptance rate, reply time, sales and
    cancellations -- the actionable set, never shown to businesses."""
    from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository

    return StockOrderRepository.performance_stats_for_supplier(profile.id)


def _supplier_last_active_iso(profile) -> str | None:
    """This supplier's own last_active_at, ISO-formatted.

    Only ever returned to the supplier THEMSELVES (this is the
    /my-profile DTO) -- the business-facing side has its own gate on
    show_last_active. A supplier can always see their own activity,
    regardless of whether they've chosen to show it to anyone.
    """
    from src.domains.auth.models.user import User

    user = User.query.filter_by(id=profile.supplier_id).first()
    if user is None or user.last_active_at is None:
        return None
    return user.last_active_at.isoformat()


def _to_dto(profile) -> dict:
    return {
        "businessName": profile.business_name,
        "category": profile.category,
        "location": profile.location,
        "description": profile.description,
        "photoVisibility": profile.photo_visibility.value,
        "visibleImageSource": profile.visible_image_source.value,
        "businessImageUrl": profile.business_image_url,
        "coverImageUrl": profile.cover_image_url,
        "whatsappNumber": profile.whatsapp_number,
        "contactEmail": profile.contact_email,
        "tiktokHandle": profile.tiktok_handle,
        "shareContactDetails": profile.share_contact_details,
        "offersDelivery": profile.offers_delivery,
        "minimumOrderCents": profile.minimum_order_cents,
        "showLastActive": profile.show_last_active,
        # The supplier's OWN last-active timestamp, so the settings row
        # can show them exactly what a business would see. Read off the
        # user row, never stored on the profile (see that column's own
        # comment on why it isn't copied).
        "lastActiveAt": _supplier_last_active_iso(profile),
        "showTrackRecord": profile.show_track_record,
        # The supplier's OWN performance figures -- a different set from
        # what businesses see (see the repository's own note on why).
        # Always returned regardless of showTrackRecord: that switch
        # controls what BUSINESSES see, never whether a supplier can see
        # their own numbers.
        "performance": _performance_stats(profile),
        "collectionBuilding": profile.collection_building,
        "collectionStreet": profile.collection_street,
        "collectionSuburb": profile.collection_suburb,
        "collectionCity": profile.collection_city,
        "collectionProvince": profile.collection_province,
        "collectionPostalCode": profile.collection_postal_code,
        "collectionLatitude": float(profile.collection_latitude) if profile.collection_latitude is not None else None,
        "collectionLongitude": float(profile.collection_longitude)
        if profile.collection_longitude is not None
        else None,
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


# --- Profile / cover image upload -------------------------------------------


@supplier_profile_bp.route("/api/v1/supplier-discovery/my-profile/images/upload-signature", methods=["POST"])
@fully_authenticated
@role_required("supplier")
@limiter.limit(
    products_rate_limit_policies.MEDIA_SIGN,
    key_func=products_rate_limit_policies.supplier_key_func,
)
def request_profile_image_upload_signature():
    payload = request.get_json(silent=True) or {}
    try:
        data = ProfileImageSignatureSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    signed = supplier_profile_image_service.request_upload_signature(_supplier_profile_id(), data["slot"])
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


@supplier_profile_bp.route("/api/v1/supplier-discovery/my-profile/images", methods=["POST"])
@fully_authenticated
@role_required("supplier")
def register_profile_image():
    payload = request.get_json(silent=True) or {}
    try:
        data = RegisterProfileImageSchema().load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_marshmallow_errors(exc), status_code=422)

    image = supplier_profile_image_service.register_uploaded_image(
        supplier_profile_id=_supplier_profile_id(),
        slot=data["slot"],
        cloudinary_public_id=data["cloudinary_public_id"],
        secure_url=data["secure_url"],
        resource_type=data["resource_type"],
        format=data["format"],
        width=data["width"],
        height=data["height"],
        bytes_=data["bytes"],
    )
    return success_response(
        data={"slot": image.slot, "secureUrl": image.secure_url, "scanStatus": image.scan_status},
        status_code=201,
    )


@supplier_profile_bp.route("/api/v1/supplier-discovery/my-profile/images/<slot>", methods=["DELETE"])
@fully_authenticated
@role_required("supplier")
def remove_profile_image(slot: str):
    supplier_profile_image_service.remove_image(_supplier_profile_id(), slot)
    return success_response(data={"slot": slot})
