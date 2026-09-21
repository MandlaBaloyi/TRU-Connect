"""
GET /api/v1/catalogue/browse -- stock, across every visible supplier.

THE CATALOGUE'S FIRST HTTP SURFACE. Until now it had none: matching ran
inside imports and the review queue lived in the CLI, so nothing about
the catalogue was ever reachable from the app. That is why tapping a
category chip went to supplier search.

THIN, like every route here: read the caller, call the service, wrap it.
No composition decision is made in this file.

PARTICIPANTS ONLY, NOT BUSINESS ONLY. A supplier browsing the catalogue
is a reasonable thing to want -- it is how they see what the market
carries -- and nothing here exposes anything a business could not see.
What differs is that a BUSINESS gets its own suppliers' offers preferred
within a group, which needs their id, so the id is passed only for them.
"""
from __future__ import annotations

import uuid

from flask import Blueprint, request
from flask_jwt_extended import get_jwt, get_jwt_identity

from src.core.decorators import fully_authenticated, participants_only
from src.core.responses import success_response
from src.domains.catalogue.discovery.services import browse_service

catalogue_browse_bp = Blueprint("catalogue_browse", __name__)

#: A page a phone can render and a metered connection can afford.
DEFAULT_LIMIT = 24
MAX_LIMIT = 60


@catalogue_browse_bp.route("/api/v1/catalogue/browse", methods=["GET"])
@fully_authenticated
@participants_only
def browse():
    role = get_jwt().get("role")

    # CLAMPED, NOT TRUSTED. A limit from a query string is a caller
    # asking the database to do arbitrary work on their behalf.
    try:
        limit = int(request.args.get("limit", DEFAULT_LIMIT))
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT
    limit = max(1, min(limit, MAX_LIMIT))

    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0

    business_id = uuid.UUID(get_jwt_identity()) if role == "business" else None

    result = browse_service.browse_category(
        business_id=business_id,
        category=request.args.get("category") or None,
        search=request.args.get("search") or None,
        kind=(request.args.get("kind") or "").strip().upper() or None,
        supplier=request.args.get("supplier") or None,
        # ONLY A BUSINESS HAS SUPPLIERS, so a supplier asking for "mine"
        # is asking a question with no answer rather than a question
        # that should fail. It is ignored, and they see the market.
        mine_only=request.args.get("mine") == "true" and business_id is not None,
        # VALIDATED AGAINST THE LIST, NOT PASSED THROUGH. The value ends
        # up choosing an ORDER BY, and the repository falls back to name
        # for anything it does not recognise -- so an unknown sort is a
        # boring page rather than an error a shopper caused by tapping.
        sort=request.args.get("sort") or "name",
        limit=limit,
        offset=offset,
    )
    return success_response(data=result)
