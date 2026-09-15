"""
Explore HTTP routes.

BUSINESS ONLY. This is a buyer browsing sellers; a supplier calling it
would be browsing their own competitors, which is a different product
with different privacy rules and is not this one.

THIN, like every route here: read the caller, call the service, wrap in
the envelope. The filter, the curtain and the ordering are all one file
over in services/.
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import success_response
from src.domains.network.community.business.cards import feed_suppliers
from src.domains.network.community.business.queries import connected_supplier_ids
from src.domains.network.community.explore.services import explore_service

explore_bp = Blueprint("community_explore", __name__)


@explore_bp.route("/api/v1/community/explore", methods=["GET"])
@fully_authenticated
@role_required("business")
def explore():
    """Suppliers of one kind, with something to sell."""
    business_id = get_jwt_identity()
    kind = (request.args.get("kind") or "").strip().upper() or None

    profiles = explore_service.wholesalers(business_id, kind=kind)
    connected = connected_supplier_ids(business_id)

    return success_response(
        data={
            # THE SAME CARD SHAPE THE FEED USES, so one component
            # renders both and a supplier cannot look different here
            # from how they look in a rail.
            "suppliers": feed_suppliers(
                profiles[: explore_service.PAGE_SIZE], connected_ids=connected
            ),
            "kinds": explore_service.kinds_with_suppliers(),
            "total": len(profiles),
        }
    )
