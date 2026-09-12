"""
Community feed HTTP routes.

ONE ENDPOINT, BOTH ROLES. V2_04 Part 5 writes it as
`?role=business` / `?role=supplier`, and the role is taken from the
TOKEN rather than the query string -- a role a caller can ask for is a
role a caller can lie about, and the two feeds are different privacy
surfaces. The query parameter would be a suggestion; the claim is a
fact.

@participants_only, not role_required: both trading roles have a feed,
and staff have none. Exactly the case that decorator exists for.

THIN, like every route in this codebase: read the caller, call the
service, wrap in the envelope. The composition rules are one file over
in services/, and no ordering decision is made here.
"""
from __future__ import annotations

from flask import Blueprint
from flask_jwt_extended import get_jwt, get_jwt_identity

from src.core.decorators import fully_authenticated, participants_only
from src.core.responses import success_response
from src.domains.network.community.services import feed_service

community_bp = Blueprint("community", __name__)


@community_bp.route("/api/v1/community/feed", methods=["GET"])
@fully_authenticated
@participants_only
def community_feed():
    role = get_jwt().get("role")
    sections = feed_service.feed_for(get_jwt_identity(), role)
    return success_response(data={"sections": sections})
