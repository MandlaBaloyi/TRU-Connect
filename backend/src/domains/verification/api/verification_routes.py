"""
Verification HTTP routes.

ONE ENDPOINT IN PHASE 1, and it is the supplier asking about
themselves. There is deliberately no staff-facing HTTP surface yet:
approving a supplier happens through `flask verification approve`,
because the control centre does not exist and an unfinished admin API
is a bigger risk than a terminal command (V2_12 Phase 1).

There is also no SUBMIT endpoint. Phase 1 holds no documents at all --
that is the whole reason it can ship before the intake pipeline is
designed.

AUTH: @fully_authenticated + @role_required("supplier"). A business has
no verification state of their own -- V2_03 Part 4.1 is explicit that
verification is a supplier problem, and a business is never asked for
documents, ID or a permit by us.
"""
from __future__ import annotations

from flask import Blueprint
from flask_jwt_extended import get_jwt_identity

from src.core.decorators import fully_authenticated, role_required
from src.core.responses import success_response
from src.domains.verification.services import verification_service

verification_bp = Blueprint("verification", __name__)


@verification_bp.route("/api/v1/verification/me", methods=["GET"])
@fully_authenticated
@role_required("supplier")
def my_verification_status():
    """Where do I stand, and can buyers see me?

    THE SHAPE IS BUILT FOR THE BANNER, not for a debugger. It returns
    the headline and detail text the app shows, rather than a raw
    status the client has to translate -- so the wording of something
    a supplier reads on every screen lives in one place and can be
    fixed without an app release.

    V2_03 Part 4.5 is specific about that wording: "your shop is ready
    and nobody can see it yet", never "you are not verified". The
    second reads as a scolding to somebody who has just spent an hour
    building a catalogue, and it is also less true -- their work is
    real, it is the visibility that is pending.
    """
    data = verification_service.get_status(get_jwt_identity())
    return success_response(data=data)
