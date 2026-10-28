"""
The one endpoint the signup gate reads.

WHY THE DEMAND DOMAIN OWNS A ROUTE AT ALL. Everything else here is
called by the feed composer and never by a client. This is the
exception because the question is genuinely the engine's: "has this
shop told me enough to be worth running on". Putting it on the profile
blueprint would have meant the profile domain holding a list of which
answers the engine needs, which is the one thing that must not exist in
two places.

READ ONLY, AND THAT IS THE DESIGN. The setup screens WRITE through the
existing /api/v1/business-profile PATCH routes -- same service, same
validation, same audit path as editing the same field in My Business
later. This endpoint only ever answers what is still missing.

ROLE IS PINNED, like every authenticated route in this backend. The
question has no meaning for a supplier: they have no buys_categories
and no restock rhythm, so an unpinned route would hand them a shape of
answer that describes a shop they are not. Project rule: "authenticated"
stopped meaning "is a buyer" the moment ADMIN existed.
"""
from __future__ import annotations

from flask import Blueprint
from flask_jwt_extended import get_jwt_identity

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import success_response
from src.domains.business.demand.services import setup_service

demand_setup_bp = Blueprint("demand_setup", __name__)


@demand_setup_bp.route("/api/v1/business/setup-state", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_setup_state():
    """Which of the three setup steps this shop has answered.

    business_id comes from the token, never from the request -- same
    non-negotiable rule as every other business-domain route.
    """
    return success_response(data=setup_service.setup_state(get_jwt_identity()))
