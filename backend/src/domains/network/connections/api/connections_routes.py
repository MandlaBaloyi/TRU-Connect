"""
Supplier Discovery HTTP routes -- file.txt Phase 1/2.

AUTH: @fully_authenticated + @role_required("business") stacked on
every route here. fully_authenticated's real location (src.core.
decorators) was VERIFIED directly against the file this time (loan_book_
routes.py/order_book_routes.py flagged it as unconfirmed; it's
confirmed now, so this file doesn't repeat that caveat).

role_required IS NOT USED ANYWHERE ELSE in this codebase (confirmed by
searching every domain) -- loan_book/order_book/business_profile only
ever check fully_authenticated, implicitly relying on a supplier
account having no plausible reason to call a business-only endpoint.
That gap is tolerable there. It is NOT tolerable here: this is the
first domain where BOTH roles are real, valid JWT holders and where
"which side of the network is this account on" has actual
consequences (a supplier account requesting a "connection" to another
supplier, as if it were a business, is a genuine authorization bug,
not just an unlikely accident). Hence the first real use of
role_required in this codebase -- not a new pattern, an existing tool
finally applied where it's actually needed.

business_id is taken from get_jwt_identity() ONLY -- never from the
request body or URL, same rule as every other route in this codebase
(see loan_book_routes.py's own docstring for the full reasoning).
"""
from __future__ import annotations

import uuid

from flask import Blueprint, request

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import success_response
from src.domains.network.connections.rate_limit import policies as rate_limit_policies
from src.domains.network.connections.services import (
    connection_list_service,
    discovery_service,
    invitation_service,
    report_service,
    request_service,
)
# Everything a BUSINESS sees of a supplier lives in its own package --
# see services/storefront/__init__.py for why the old single
# catalog_service.py was split.
from src.domains.network.connections.services.storefront import (
    catalog_service,
    showcase_service,
)
from src.domains.security.rate_limit.limiter import limiter

connections_bp = Blueprint("connections", __name__)


def _business_id() -> uuid.UUID:
    from flask_jwt_extended import get_jwt_identity

    return uuid.UUID(get_jwt_identity())


def _supplier_id() -> uuid.UUID:
    from flask_jwt_extended import get_jwt_identity

    return uuid.UUID(get_jwt_identity())


@connections_bp.route("/api/v1/supplier-discovery/search", methods=["GET"])
@fully_authenticated
@role_required("business")
@limiter.limit(rate_limit_policies.SEARCH, key_func=rate_limit_policies.business_key_func)
def search():
    query = request.args.get("q", "")
    results = discovery_service.search_suppliers(query, _business_id())
    return success_response(data={"results": results})


@connections_bp.route("/api/v1/supplier-discovery/suppliers/<uuid:supplier_profile_id>", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_supplier_profile(supplier_profile_id: uuid.UUID):
    profile = discovery_service.get_supplier_profile(_business_id(), supplier_profile_id)
    return success_response(data=profile)


@connections_bp.route(
    "/api/v1/supplier-discovery/suppliers/<uuid:supplier_profile_id>/products/categories", methods=["GET"]
)
@fully_authenticated
@role_required("business")
def get_supplier_product_categories(supplier_profile_id: uuid.UUID):
    categories = catalog_service.get_supplier_product_categories(supplier_profile_id)
    return success_response(data={"categories": categories})


@connections_bp.route(
    "/api/v1/supplier-discovery/suppliers/<uuid:supplier_profile_id>/profile-products", methods=["GET"]
)
@fully_authenticated
@role_required("business")
def list_supplier_profile_products(supplier_profile_id: uuid.UUID):
    """The small pinned/featured strip on the supplier's brand profile
    -- distinct from the paginated /products catalogue below."""
    result = showcase_service.list_profile_products(_business_id(), supplier_profile_id)
    return success_response(data=result)


@connections_bp.route("/api/v1/supplier-discovery/suppliers/<uuid:supplier_profile_id>/products", methods=["GET"])
@fully_authenticated
@role_required("business")
def list_supplier_products(supplier_profile_id: uuid.UUID):
    # Same simple request.args.get pattern already used for the search
    # routes in this file (e.g. search_suppliers' own "q" param) --
    # real validation (range/allowed-values checks) happens in the
    # service layer, not here.
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=catalog_service.DEFAULT_CATALOG_PAGE_SIZE, type=int)
    sort = request.args.get("sort", default="NEWEST")
    category = request.args.get("category")

    result = catalog_service.list_supplier_products(
        _business_id(), supplier_profile_id, page=page, limit=limit, sort=sort, category=category
    )
    return success_response(data=result)


@connections_bp.route(
    "/api/v1/supplier-discovery/suppliers/<uuid:supplier_profile_id>/products/<uuid:product_id>",
    methods=["GET"],
)
@fully_authenticated
@role_required("business")
def get_supplier_product(supplier_profile_id: uuid.UUID, product_id: uuid.UUID):
    product = catalog_service.get_supplier_product(_business_id(), supplier_profile_id, product_id)
    return success_response(data=product)


@connections_bp.route(
    "/api/v1/supplier-discovery/suppliers/<uuid:supplier_profile_id>/products/<uuid:product_id>/related",
    methods=["GET"],
)
@fully_authenticated
@role_required("business")
def list_related_products(supplier_profile_id: uuid.UUID, product_id: uuid.UUID):
    result = catalog_service.list_related_products(_business_id(), supplier_profile_id, product_id)
    return success_response(data=result)


@connections_bp.route(
    "/api/v1/supplier-discovery/suppliers/<uuid:supplier_profile_id>/connection-requests", methods=["POST"]
)
@fully_authenticated
@role_required("business")
@limiter.limit(rate_limit_policies.CONNECTION_REQUEST, key_func=rate_limit_policies.business_key_func)
def request_connection(supplier_profile_id: uuid.UUID):
    result = request_service.request_connection(_business_id(), supplier_profile_id)
    return success_response(data=result)


# ---------------------------------------------------------------------------
# Find Business -- the reverse direction. role_required("supplier") is
# the mirror of the business-only routes above, same reasoning.
# ---------------------------------------------------------------------------


@connections_bp.route("/api/v1/supplier-discovery/businesses/search", methods=["GET"])
@fully_authenticated
@role_required("supplier")
@limiter.limit(rate_limit_policies.SEARCH, key_func=rate_limit_policies.business_key_func)
def search_businesses():
    query = request.args.get("q", "")
    results = discovery_service.search_businesses(query, _supplier_id())
    return success_response(data={"results": results})


@connections_bp.route("/api/v1/supplier-discovery/businesses/<uuid:business_profile_id>", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_business_profile(business_profile_id: uuid.UUID):
    profile = discovery_service.get_business_profile(_supplier_id(), business_profile_id)
    return success_response(data=profile)


@connections_bp.route(
    "/api/v1/supplier-discovery/businesses/<uuid:business_profile_id>/connection-requests", methods=["POST"]
)
@fully_authenticated
@role_required("supplier")
@limiter.limit(rate_limit_policies.CONNECTION_REQUEST, key_func=rate_limit_policies.business_key_func)
def request_connection_to_business(business_profile_id: uuid.UUID):
    result = request_service.request_connection_to_business(_supplier_id(), business_profile_id)
    return success_response(data=result)


# ---------------------------------------------------------------------------
# Supplier-side -- file.txt Phase 3 / FILE2.txt "PHASE 3 -- SUPPLIER
# APPROVAL". role_required("supplier") is the mirror image of the
# business-only routes above, same reasoning (see this file's own top
# docstring).
# ---------------------------------------------------------------------------


@connections_bp.route("/api/v1/supplier-discovery/customer-requests", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_customer_requests():
    results = request_service.get_customer_requests(_supplier_id())
    return success_response(data={"requests": results})


@connections_bp.route("/api/v1/supplier-discovery/customer-requests/<uuid:request_id>", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def get_customer_request_detail(request_id: uuid.UUID):
    detail = request_service.get_customer_request_detail(_supplier_id(), request_id)
    return success_response(data=detail)


@connections_bp.route(
    "/api/v1/supplier-discovery/customer-requests/<uuid:request_id>/approve", methods=["POST"]
)
@fully_authenticated
@role_required("supplier")
def approve_customer_request(request_id: uuid.UUID):
    result = request_service.approve_request(_supplier_id(), request_id)
    return success_response(data=result)


@connections_bp.route(
    "/api/v1/supplier-discovery/customer-requests/<uuid:request_id>/decline", methods=["POST"]
)
@fully_authenticated
@role_required("supplier")
def decline_customer_request(request_id: uuid.UUID):
    result = request_service.decline_request(_supplier_id(), request_id)
    return success_response(data=result)


# ---------------------------------------------------------------------------
# Business-side: Supplier Requests -- the mirror of Customer Requests
# above. SUPPLIER-initiated requests the business owes an approval on
# (Find Business's own "connect" action). role_required("business") is
# the mirror of the supplier-only routes above, same reasoning.
# ---------------------------------------------------------------------------


@connections_bp.route("/api/v1/supplier-discovery/supplier-requests", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_supplier_requests():
    results = request_service.get_supplier_requests(_business_id())
    return success_response(data={"requests": results})


@connections_bp.route("/api/v1/supplier-discovery/supplier-requests/<uuid:request_id>", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_supplier_request_detail(request_id: uuid.UUID):
    detail = request_service.get_supplier_request_detail(_business_id(), request_id)
    return success_response(data=detail)


@connections_bp.route(
    "/api/v1/supplier-discovery/supplier-requests/<uuid:request_id>/approve", methods=["POST"]
)
@fully_authenticated
@role_required("business")
def approve_supplier_request(request_id: uuid.UUID):
    result = request_service.approve_supplier_request(_business_id(), request_id)
    return success_response(data=result)


@connections_bp.route(
    "/api/v1/supplier-discovery/supplier-requests/<uuid:request_id>/decline", methods=["POST"]
)
@fully_authenticated
@role_required("business")
def decline_supplier_request(request_id: uuid.UUID):
    result = request_service.decline_supplier_request(_business_id(), request_id)
    return success_response(data=result)


# ---------------------------------------------------------------------------
# Supplier Invitation -- file.txt Phase 2. invite_supplier is
# business-only (the mirror of every other business-only route above).
# validate_invitation is DELIBERATELY UNAUTHENTICATED -- no
# @fully_authenticated, no @role_required -- the whole point is a
# person who doesn't have an account yet can check whether their
# invite link still works before registering. Same reasoning as
# PasswordResetService.validate_ticket's own route: the ticket itself
# is the credential, matching this codebase's existing precedent.
# ---------------------------------------------------------------------------


@connections_bp.route("/api/v1/supplier-discovery/invitations", methods=["POST"])
@fully_authenticated
@role_required("business")
def invite_supplier():
    from marshmallow import ValidationError as MarshmallowValidationError

    from src.core.responses import error_response
    from src.domains.network.connections.schemas.connections_schemas import InviteContactSchema

    payload = request.get_json(silent=True) or {}
    try:
        data = InviteContactSchema().load(payload)
    except MarshmallowValidationError as exc:
        # Flattened to a list -- error_response's own signature expects
        # `errors: Optional[list]`, matching auth/api/routes.py's own
        # _flatten_errors convention (not loan_book_routes.py's, which
        # bypasses error_response and jsonify()s the raw dict directly).
        flat_errors = [
            str(msg)
            for field_errors in exc.messages.values()
            for msg in (field_errors if isinstance(field_errors, list) else [field_errors])
        ]
        return error_response(message="Validation failed", errors=flat_errors, status_code=422)

    result = invitation_service.invite_supplier(_business_id(), data["email"])
    return success_response(data=result)


@connections_bp.route("/api/v1/supplier-discovery/business-invitations", methods=["POST"])
@fully_authenticated
@role_required("supplier")
def invite_business():
    from marshmallow import ValidationError as MarshmallowValidationError

    from src.core.responses import error_response
    from src.domains.network.connections.schemas.connections_schemas import InviteContactSchema

    payload = request.get_json(silent=True) or {}
    try:
        data = InviteContactSchema().load(payload)
    except MarshmallowValidationError as exc:
        flat_errors = [
            str(msg)
            for field_errors in exc.messages.values()
            for msg in (field_errors if isinstance(field_errors, list) else [field_errors])
        ]
        return error_response(message="Validation failed", errors=flat_errors, status_code=422)

    result = invitation_service.invite_business(_supplier_id(), data["email"])
    return success_response(data=result)


@connections_bp.route("/api/v1/supplier-discovery/invitations/validate", methods=["GET"])
def validate_invitation():
    ticket = request.args.get("ticket", "")
    is_valid = invitation_service.validate_invitation(ticket) if ticket else False
    return success_response(data={"valid": is_valid})


@connections_bp.route("/api/v1/supplier-discovery/connections", methods=["GET"])
@fully_authenticated
def get_my_connections():
    """My Connections -- Community tab, both roles. Deliberately NOT
    role_required("business") or role_required("supplier") like every
    other route in this file -- see connection_list_service.py's own
    get_my_connections docstring on why one shared route branching on
    the caller's own role is the honest design here, not a shortcut."""
    from flask_jwt_extended import get_jwt, get_jwt_identity

    role = get_jwt().get("role")
    user_id = uuid.UUID(get_jwt_identity())
    results = connection_list_service.get_my_connections(user_id, role)
    return success_response(data={"connections": results})


@connections_bp.route("/api/v1/supplier-discovery/my-photo-settings", methods=["PATCH"])
@fully_authenticated
def update_my_photo_settings():
    """Same shared-route reasoning as get_my_connections above."""
    from flask_jwt_extended import get_jwt, get_jwt_identity

    role = get_jwt().get("role")
    user_id = uuid.UUID(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    result = discovery_service.update_my_photo_settings(
        user_id,
        role,
        visible_image_source=payload.get("visibleImageSource"),
        photo_visibility=payload.get("photoVisibility"),
    )
    return success_response(data=result)


@connections_bp.route(
    "/api/v1/supplier-discovery/suppliers/<uuid:supplier_profile_id>/disconnect", methods=["POST"]
)
@fully_authenticated
@role_required("business")
def end_connection(supplier_profile_id: uuid.UUID):
    from marshmallow import ValidationError as MarshmallowValidationError

    from src.core.responses import error_response
    from src.domains.network.connections.schemas.connections_schemas import EndConnectionSchema

    payload = request.get_json(silent=True) or {}
    try:
        data = EndConnectionSchema().load(payload)
    except MarshmallowValidationError as exc:
        errors = [str(msg) for field_errors in exc.messages.values() for msg in field_errors]
        return error_response(message="Validation failed", errors=errors, status_code=422)

    # ConnectionRequestNotFoundError/ConnectionNotActiveError aren't
    # caught here -- same as every other route in this file, a
    # global error handler already converts them to the real status
    # code.
    result = connection_list_service.end_connection(_business_id(), supplier_profile_id, data["reason"], data["details"])
    return success_response(data=result)


@connections_bp.route("/api/v1/supplier-discovery/connections/ended", methods=["GET"])
@fully_authenticated
@role_required("business")
def list_ended_connections():
    """Business-only -- the "who have I disconnected from" list has no
    equivalent concept on the supplier side yet (a supplier ending a
    relationship isn't a flow this pass builds), so unlike
    get_my_connections above, this one doesn't need to branch on
    role."""
    results = connection_list_service.list_ended_connections(_business_id())
    return success_response(data={"connections": results})


@connections_bp.route("/api/v1/supplier-discovery/suppliers/<uuid:supplier_profile_id>/report", methods=["POST"])
@fully_authenticated
@role_required("business")
def report_supplier(supplier_profile_id: uuid.UUID):
    from marshmallow import ValidationError as MarshmallowValidationError

    from src.core.responses import error_response
    from src.domains.network.connections.schemas.connections_schemas import ReportSupplierSchema

    payload = request.get_json(silent=True) or {}
    try:
        data = ReportSupplierSchema().load(payload)
    except MarshmallowValidationError as exc:
        errors = [str(msg) for field_errors in exc.messages.values() for msg in field_errors]
        return error_response(message="Validation failed", errors=errors, status_code=422)

    result = report_service.report_supplier(
        _business_id(), supplier_profile_id, data["reason"], data["details"], product_id=data["product_id"]
    )
    return success_response(data=result)
