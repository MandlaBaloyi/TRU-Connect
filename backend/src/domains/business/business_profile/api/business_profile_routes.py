"""
Business Profile HTTP routes.

AUTH: @fully_authenticated + @role_required("business"), same as Loan
Book and Order Book.

THE ROLE CHECK MATTERS MORE HERE THAN ANYWHERE ELSE IN THE DOMAIN,
because GET /business-profile is a read that WRITES: get_profile calls
BusinessProfileRepository.get_or_create_for_business. With no role
pinned, merely LOOKING at this endpoint with a supplier's or a staff
token created a BusinessProfile row keyed to them -- no error, no
audit entry, just an account that is now also a business to every
query that joins on this table.

business_id is taken from get_jwt_identity() -- the authenticated
caller's own user id -- NEVER from anything in the request body or
URL. Same non-negotiable rule as every other business-domain route in
this backend.

ONE PATCH ROUTE PER SECTION, matching the frontend's
useBusinessProfileMutations exactly (one mutation per section, never a
single save-everything call). Each PATCH accepts a partial body --
only the fields present get updated, everything else on the profile is
left untouched -- matching Partial<T> on the frontend's mutation
input types.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated, role_required
from src.domains.business.business_profile.schemas.business_profile_schemas import (
    UpdateBusinessDetailsSchema,
    UpdateContactDetailsSchema,
    UpdateLocationSchema,
    UpdateOperatingHistorySchema,
    UpdateSupplierInfoSchema,
    UpdateTradingDetailsSchema,
)
from src.domains.business.business_profile.services.business_profile_service import BusinessProfileService
from src.domains.business.business_profile.services.errors import BusinessProfileValidationError

business_profile_bp = Blueprint("business_profile", __name__)


def _business_id():
    return get_jwt_identity()


@business_profile_bp.route("/api/v1/business-profile", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_profile():
    return jsonify(success=True, data=BusinessProfileService.get_profile(_business_id()))


def _handle_update(schema_cls, service_fn):
    """Shared shape for every PATCH route below: validate (partial),
    call the matching service function, return the full refreshed
    profile -- exactly what the frontend's mutations expect back
    (Promise<BusinessProfile>, not just the changed section)."""
    try:
        data = schema_cls(partial=True).load(request.get_json(force=True) or {})
    except MarshmallowValidationError as e:
        return jsonify(success=False, message="Invalid input.", errors=e.messages), 422

    try:
        profile = service_fn(_business_id(), data)
    except BusinessProfileValidationError as e:
        return jsonify(success=False, message=e.message, errors=[{"field": e.field, "message": e.message}] if e.field else []), 422

    return jsonify(success=True, data=profile)


@business_profile_bp.route("/api/v1/business-profile/business-details", methods=["PATCH"])
@fully_authenticated
@role_required("business")
def update_business_details():
    return _handle_update(UpdateBusinessDetailsSchema, BusinessProfileService.update_business_details)


@business_profile_bp.route("/api/v1/business-profile/contact-details", methods=["PATCH"])
@fully_authenticated
@role_required("business")
def update_contact_details():
    return _handle_update(UpdateContactDetailsSchema, BusinessProfileService.update_contact_details)


@business_profile_bp.route("/api/v1/business-profile/location", methods=["PATCH"])
@fully_authenticated
@role_required("business")
def update_location():
    return _handle_update(UpdateLocationSchema, BusinessProfileService.update_location)


@business_profile_bp.route("/api/v1/business-profile/trading-details", methods=["PATCH"])
@fully_authenticated
@role_required("business")
def update_trading_details():
    return _handle_update(UpdateTradingDetailsSchema, BusinessProfileService.update_trading_details)


@business_profile_bp.route("/api/v1/business-profile/operating-history", methods=["PATCH"])
@fully_authenticated
@role_required("business")
def update_operating_history():
    return _handle_update(UpdateOperatingHistorySchema, BusinessProfileService.update_operating_history)


@business_profile_bp.route("/api/v1/business-profile/suppliers", methods=["PATCH"])
@fully_authenticated
@role_required("business")
def update_supplier_info():
    return _handle_update(UpdateSupplierInfoSchema, BusinessProfileService.update_supplier_info)
