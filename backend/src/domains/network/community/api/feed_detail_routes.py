"""
The screens behind the feed's arrows.

FIVE ENDPOINTS, ONE SHAPE. Each returns a page of the same ranked set
its rail previews, so a "see all" can never disagree with the rail it
opened from -- the ranking lives in feed_detail_service and both
surfaces read it.

BUSINESS ONLY, and that is not an oversight. Every one of these answers
a question about a SHOP -- what it bought, what it needs, who is near
it. The supplier feed asks different questions and has no equivalent
screens; `participants_only` would have let a supplier call them and
get somebody else's shape of answer, or an empty one, which is a worse
failure than a clean 403.

    EVERY AUTHENTICATED ROUTE PINS A ROLE (CLAUDE.md). role_required
    here rather than participants_only, because "authenticated" stopped
    meaning "is a buyer" the moment ADMIN existed.

THIN, like every route in this codebase: read the caller, read the
paging, call the service, wrap in the envelope. No ordering decision is
made here and no ceiling is applied here.
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import success_response
from src.domains.network.community.business.cards import feed_suppliers
from src.domains.network.community.business.queries import connected_supplier_ids
from src.domains.network.community.services import feed_detail_service

feed_detail_bp = Blueprint("community_detail", __name__)


def _paging() -> tuple:
    """limit and offset, clamped in the service rather than trusted.

    A CALLER ASKING FOR TEN THOUSAND gets PAGE_SIZE, not an error: the
    request is not malicious, it is a client with a different idea of a
    page, and refusing it would break a screen over a number nobody
    chose deliberately.
    """
    try:
        limit = int(request.args.get("limit", feed_detail_service.PAGE_SIZE))
    except (TypeError, ValueError):
        limit = feed_detail_service.PAGE_SIZE
    try:
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0
    return limit, offset


@feed_detail_bp.route("/api/v1/community/buy-it-again", methods=["GET"])
@fully_authenticated
@role_required("business")
def buy_it_again():
    """Everything this shop has ordered before, most recent first.

    NO PER-SUPPLIER CEILING AT ANY LENGTH -- their own history, in the
    order they bought it (V2_17 Q3).
    """
    limit, offset = _paging()
    cards = feed_detail_service.buy_it_again_cards(get_jwt_identity())
    page = feed_detail_service.paginate(cards, limit=limit, offset=offset)
    return success_response(
        data={"products": page["items"], "hasMore": page["hasMore"], "total": page["total"]}
    )


@feed_detail_bp.route("/api/v1/community/moving-fast", methods=["GET"])
@fully_authenticated
@role_required("business")
def moving_fast():
    """Products rising faster than their own past, in this shop's
    categories.

    CEILING APPLIED, unlike buy-it-again: this rail RECOMMENDS, and a
    screen of one wholesaler's spike is that wholesaler's news rather
    than the market's.
    """
    from src.domains.network.community.algorithms import interleave

    limit, offset = _paging()
    cards = feed_detail_service.moving_fast_cards(get_jwt_identity())
    # Capped and interleaved across the WHOLE set before paging, so the
    # ceiling means the same thing on page three as on page one.
    cards = interleave.arrange(cards, absolute_cap=5)
    page = feed_detail_service.paginate(cards, limit=limit, offset=offset)
    return success_response(
        data={"products": page["items"], "hasMore": page["hasMore"], "total": page["total"]}
    )


@feed_detail_bp.route("/api/v1/community/stock-for-you", methods=["GET"])
@fully_authenticated
@role_required("business")
def stock_for_you():
    """The demand engine's full answer, strongest need first."""
    from src.domains.network.community.algorithms import interleave

    limit, offset = _paging()
    cards = feed_detail_service.stock_for_you_cards(get_jwt_identity())
    cards = interleave.arrange(cards, absolute_cap=5)
    page = feed_detail_service.paginate(cards, limit=limit, offset=offset)
    return success_response(
        data={"products": page["items"], "hasMore": page["hasMore"], "total": page["total"]}
    )


@feed_detail_bp.route("/api/v1/community/collect-near-you", methods=["GET"])
@fully_authenticated
@role_required("business")
def collect_near_you():
    """Suppliers inside the collection radius, nearest first.

    STRICTLY DISTANCE-ORDERED, at every tier, forever. This is the only
    surface that prints the number it is sorted by, so any reordering is
    a contradiction the reader is holding (V2_17 Q5).
    """
    business_id = get_jwt_identity()
    limit, offset = _paging()

    measured = feed_detail_service.collect_near_you_suppliers(business_id)
    page = feed_detail_service.paginate(measured, limit=limit, offset=offset)
    connected = connected_supplier_ids(business_id)

    return success_response(
        data={
            "suppliers": feed_suppliers(
                [profile for _, profile in page["items"]],
                distances={profile.id: round(km, 1) for km, profile in page["items"]},
                connected_ids=connected,
            ),
            "hasMore": page["hasMore"],
            "total": page["total"],
        }
    )


@feed_detail_bp.route("/api/v1/community/not-ordered-yet", methods=["GET"])
@fully_authenticated
@role_required("business")
def not_ordered_yet():
    """Visible suppliers with stock this shop has never bought from."""
    business_id = get_jwt_identity()
    limit, offset = _paging()

    untried = feed_detail_service.not_ordered_yet_suppliers(business_id)
    page = feed_detail_service.paginate(untried, limit=limit, offset=offset)
    connected = connected_supplier_ids(business_id)

    return success_response(
        data={
            "suppliers": feed_suppliers(page["items"], connected_ids=connected),
            "hasMore": page["hasMore"],
            "total": page["total"],
        }
    )
