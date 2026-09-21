"""
The one thing the device knows and the server does not.

ONE ENDPOINT, AND IT ONLY ACCEPTS TAPS. `delivered` is written
server-side at compose time and is deliberately unreachable from here
-- see impression_service's own docstring. A client able to assert what
it was shown could manufacture the denominator of every tap rate in the
system, and the denominator is the half that will eventually be
billed on.

BUSINESS ONLY. A supplier's feed is a different surface with different
sections, and measuring it is a separate question that has not been
asked yet. @role_required rather than @participants_only, so the
supplier side is a deliberate future addition rather than something
that quietly started working.

RATE LIMITED FROM DAY ONE. The only write in this domain a device can
drive on a timer -- see rate_limit/policies.py for why that made this
the one limit that could not wait for the rest of the hardening pass.
"""
from __future__ import annotations

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity

from src.core.decorators import fully_authenticated, role_required
from src.core.exceptions import ValidationError
from src.core.responses import success_response
from src.domains.network.impressions.models.feed_impression import (
    ImpressionItemType,
)
from src.domains.network.impressions.rate_limit import (
    policies as rate_limit_policies,
)
from src.domains.network.impressions.repositories.impression_repository import (
    ImpressionRow,
)
from src.domains.network.impressions.services import impression_service
from src.domains.security.rate_limit.limiter import limiter
from src.shared.queue.queue import enqueue

impression_bp = Blueprint("community_impressions", __name__)


@impression_bp.route("/api/v1/community/impressions/tap", methods=["POST"])
@fully_authenticated
@role_required("business")
# THE LIMITER GOES LAST, BENEATH THE AUTH DECORATORS, and the order is
# not cosmetic. business_key_func calls get_jwt_identity(); above
# @fully_authenticated there is no verified JWT in the request context
# yet, so it raises and flask_jwt_extended turns an unauthenticated
# POST into a 500 instead of a 401. Caught by curling the endpoint with
# no token and getting the wrong number back.
#
# It also means an anonymous caller is refused by auth BEFORE consuming
# anybody's allowance, which is the right way round: there is no
# identity to key the limit by until the token has been checked. Same
# order as every rate-limited route in connections/.
@limiter.limit(rate_limit_policies.TAP, key_func=rate_limit_policies.business_key_func)
def record_taps():
    """Count taps the app batched up.

    THE SHOP COMES FROM THE TOKEN, NEVER THE PAYLOAD. This is the whole
    IDOR answer for this route: there is no field a caller could use to
    write another business's counters, because the only identity in the
    statement is the one the token proved.

    ACCEPTS A BATCH AND ANSWERS WITH A COUNT rather than echoing the
    rows back. Nothing on the device needs to know what happened here,
    and an endpoint that returns what it stored invites a client to
    start depending on it.
    """
    payload = request.get_json(silent=True) or {}
    taps = payload.get("taps")

    if not isinstance(taps, list) or not taps:
        raise ValidationError({"taps": ["A non-empty list of taps is required."]})

    if len(taps) > rate_limit_policies.MAX_TAPS_PER_REQUEST:
        # THE SECOND CEILING. The per-minute limit bounds REQUESTS; this
        # bounds ROWS, and rows are the thing the grain decision exists
        # to protect. One is not a substitute for the other.
        raise ValidationError(
            {
                "taps": [
                    "At most "
                    f"{rate_limit_policies.MAX_TAPS_PER_REQUEST} taps per request."
                ]
            }
        )

    business_id = get_jwt_identity()
    rows = [_parse(tap, index) for index, tap in enumerate(taps)]

    # ENQUEUED, NOT AWAITED, AND THE APP CONTEXT IS CARRIED IN WITH IT.
    # The queue is a ThreadPoolExecutor and a worker thread has no Flask
    # application context, so db.session raises the moment it is touched
    # and the runner swallows it to keep the pool alive -- a request
    # that returns 200 and writes nothing. The delivered side had
    # exactly this bug; see feed_service._count_delivered.
    #
    # ONE JOB FOR THE WHOLE BATCH. A job per tap would be a hundred
    # background tasks and a hundred round trips for what the repository
    # does in one statement.
    app = current_app._get_current_object()

    def _write() -> None:
        with app.app_context():
            impression_service.record_taps(business_id, rows)

    enqueue(_write)

    return success_response(message="Recorded.", data={"accepted": len(rows)})


def _parse(tap: object, index: int) -> ImpressionRow:
    """One entry, validated into the grain.

    EVERY FIELD IS REQUIRED AND THE POSITION MUST BE A REAL INDEX,
    because a tap that cannot name where it happened is worthless for
    the one question this table was built to answer -- tier_rules'
    falsifier is a tap-rate gap BETWEEN POSITIONS, and a row with a
    guessed position would answer it wrongly rather than not at all.
    """
    if not isinstance(tap, dict):
        raise ValidationError({f"taps.{index}": ["Each tap must be an object."]})

    rail = tap.get("rail")
    item_id = tap.get("itemId")
    position = tap.get("position")
    raw_type = tap.get("itemType")

    if not isinstance(rail, str) or not rail.strip():
        raise ValidationError({f"taps.{index}.rail": ["A rail id is required."]})
    if not isinstance(item_id, str) or not item_id.strip():
        raise ValidationError({f"taps.{index}.itemId": ["An item id is required."]})
    if not isinstance(position, int) or isinstance(position, bool) or position < 0:
        # bool IS an int in Python, and True would otherwise sail
        # through as position 1. It has caught people before.
        raise ValidationError(
            {f"taps.{index}.position": ["A zero-based position is required."]}
        )

    try:
        item_type = ImpressionItemType(raw_type)
    except ValueError:
        raise ValidationError(
            {
                f"taps.{index}.itemType": [
                    "Must be one of: "
                    + ", ".join(t.value for t in ImpressionItemType)
                    + "."
                ]
            }
        )

    return ImpressionRow(
        rail=rail.strip()[:64],
        position=position,
        item_id=item_id.strip()[:64],
        item_type=item_type,
        supplier_profile_id=tap.get("supplierId") or None,
    )
