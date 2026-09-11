"""
domains/network/geocoding HTTP routes -- genuinely role-agnostic, same
reasoning as notifications_routes.py's own docstring: a business picks
a delivery pin, and (once the closely-related, separate supplier-own-
pin feature exists) a supplier will pin their own collection address
too. Scoping by role would be actively wrong here, not just
unnecessary -- there's no per-user data being read or written, only a
stateless lookup, so @fully_authenticated (any logged-in user) is the
whole auth story. Never @role_required.
"""
from __future__ import annotations

from flask import Blueprint, request

from src.core.decorators import fully_authenticated, participants_only
from src.core.responses import error_response, success_response
from src.domains.network.geocoding.providers.composition import get_geocoding_provider
from src.domains.network.geocoding.rate_limit import policies as rate_limit_policies
from src.domains.security.rate_limit.limiter import limiter

geocoding_bp = Blueprint("geocoding", __name__)


@geocoding_bp.route("/api/v1/geocoding/reverse", methods=["GET"])
@fully_authenticated
@participants_only
@limiter.limit(rate_limit_policies.REVERSE_GEOCODE, key_func=rate_limit_policies.user_key_func)
def reverse_geocode():
    # Query params, not a JSON body -- this is a GET/lookup, not a
    # state change, same shape as any other read-only endpoint in this
    # codebase. Validated by hand rather than a marshmallow schema:
    # two required floats is genuinely simpler inline than a schema
    # file would be, matching how _load_or_422 itself is only ever
    # reached for.load()-able JSON bodies elsewhere in this codebase.
    try:
        latitude = float(request.args["latitude"])
        longitude = float(request.args["longitude"])
    except (KeyError, ValueError):
        return error_response("latitude and longitude are required and must be numbers.", status_code=422)

    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        return error_response("latitude/longitude are outside valid range.", status_code=422)

    provider = get_geocoding_provider()
    address = provider.reverse_geocode(latitude, longitude)

    return success_response(
        data={
            "building": address.building,
            "street": address.street,
            "suburb": address.suburb,
            "city": address.city,
            "province": address.province,
            "postalCode": address.postal_code,
        }
    )


@geocoding_bp.route("/api/v1/geocoding/search", methods=["GET"])
@fully_authenticated
@participants_only
@limiter.limit(rate_limit_policies.SEARCH_SUGGEST, key_func=rate_limit_policies.user_key_func)
def search_suggest():
    """Part one of the Search Box companion to the pin-drop picker --
    typeahead suggestions as the business types. session_token is
    REQUIRED, not optional -- generated client-side once per search
    session (see the frontend's own session-token helper), reused for
    every suggest call and the one retrieve call that completes it."""
    query = (request.args.get("q") or "").strip()
    session_token = (request.args.get("session_token") or "").strip()
    if not query:
        return error_response("q is required.", status_code=422)
    if not session_token:
        return error_response("session_token is required.", status_code=422)

    proximity = None
    lat_param, lng_param = request.args.get("proximity_lat"), request.args.get("proximity_lng")
    if lat_param and lng_param:
        try:
            proximity = (float(lat_param), float(lng_param))
        except ValueError:
            return error_response("proximity_lat/proximity_lng must be numbers.", status_code=422)

    provider = get_geocoding_provider()
    suggestions = provider.suggest(query, session_token, proximity)

    return success_response(
        data=[{"mapboxId": s.mapbox_id, "name": s.name, "fullAddress": s.full_address} for s in suggestions]
    )


@geocoding_bp.route("/api/v1/geocoding/search/retrieve", methods=["GET"])
@fully_authenticated
@participants_only
@limiter.limit(rate_limit_policies.SEARCH_RETRIEVE, key_func=rate_limit_policies.user_key_func)
def search_retrieve():
    """Part two -- resolves a tapped suggestion to real coordinates.
    Deliberately returns ONLY latitude/longitude, not address text --
    see MapboxGeocodingProvider.retrieve's own docstring for why."""
    mapbox_id = (request.args.get("mapbox_id") or "").strip()
    session_token = (request.args.get("session_token") or "").strip()
    if not mapbox_id:
        return error_response("mapbox_id is required.", status_code=422)
    if not session_token:
        return error_response("session_token is required.", status_code=422)

    provider = get_geocoding_provider()
    latitude, longitude = provider.retrieve(mapbox_id, session_token)

    return success_response(data={"latitude": latitude, "longitude": longitude})
