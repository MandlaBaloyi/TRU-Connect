"""
MapboxGeocodingProvider -- the ONLY file in this codebase that talks to
api.mapbox.com. Everything else depends on GeocodingProvider
(provider.py), never this class or the Mapbox HTTP API directly.

THE FIRST REAL, LIVE OUTBOUND THIRD-PARTY HTTP CALL THIS BACKEND MAKES
AT REQUEST TIME -- worth calling out explicitly rather than treating
as routine: `requests` is already a dependency, but until now it was
only ever used by a manual dev script (see requirements.txt's own
comment on verify_cloudinary_connection.py); Cloudinary's own signed
uploads are signed locally and the actual file bytes go straight from
the client to Cloudinary, never through this backend. This is
genuinely new territory for this codebase, which is why it gets an
explicit, short timeout (GeocodingConfig.request_timeout_seconds) and
never lets a Mapbox failure become an unhandled 500 -- see
reverse_geocode's own try/except below.

ENDPOINT: GET https://api.mapbox.com/search/geocode/v6/reverse --
confirmed directly against Mapbox's current API docs (v6, not the
deprecated v5 mapbox.places.json shape) before writing this, per this
project's own "verify current docs, don't trust stale training
knowledge" discipline. `permanent` is passed straight from
GeocodingConfig -- see that file's own docstring for why it defaults
to false (temporary, free) and what would need to change to flip it.

CONTEXT-OBJECT MAPPING -- v6's response nests each address component
under `properties.context`, keyed by feature type, each with its own
`name`. Mapped here as:
    context.street.name       -> street
    context.neighborhood.name -> suburb
    context.place.name        -> city
    context.region.name       -> province
    context.postcode.name     -> postal_code
`building` is never populated -- Mapbox has no such concept; see
GeocodedAddress's own docstring. NOT YET VALIDATED against real South
African village/town addresses (e.g. "Elim") -- this mapping is
Mapbox's own documented v6 shape, but coverage quality for informal
SA addresses is the explicitly-flagged next thing to test for real
before trusting this in production, same honesty this project applies
everywhere else.

SUGGEST/RETRIEVE (Search Box API) -- a SEPARATE Mapbox product family
from the Geocoding API above, confirmed directly against Mapbox's
current /suggest and /retrieve docs: different base path
(api.mapbox.com/search/searchbox/v1/...), session-token billing
(one search session, however many /suggest calls, bills as ONE unit,
not per keystroke -- see GeocodingProvider.suggest's own docstring),
and results here explicitly may NOT be stored per Mapbox's terms.
retrieve() deliberately returns ONLY coordinates, discarding the
address text Search Box's own response also contains -- once a
suggestion is picked, the picker re-centers the map there and lets
the EXISTING reverse_geocode flow fill the address fields, so there's
one single, consistent source of address-field truth regardless of
whether the business searched or panned to a spot.
"""
from __future__ import annotations

import requests

from src.domains.network.geocoding.config.geocoding_config import GeocodingConfig
from src.domains.network.geocoding.errors import GeocodingProviderError
from src.domains.network.geocoding.providers.provider import GeocodedAddress, GeocodingProvider, SearchSuggestion

_REVERSE_GEOCODE_URL = "https://api.mapbox.com/search/geocode/v6/reverse"
_SUGGEST_URL = "https://api.mapbox.com/search/searchbox/v1/suggest"
_RETRIEVE_URL_TEMPLATE = "https://api.mapbox.com/search/searchbox/v1/retrieve/{mapbox_id}"


class MapboxGeocodingProvider(GeocodingProvider):
    def __init__(self, config: GeocodingConfig):
        self._config = config

    def reverse_geocode(self, latitude: float, longitude: float) -> GeocodedAddress:
        if not self._config.access_token:
            # A missing token is a real deployment/config problem, not
            # a "no results" case -- raised distinctly so it never
            # gets silently swallowed into an empty-but-"successful"
            # GeocodedAddress the way a genuine no-match lookup does.
            raise GeocodingProviderError("Mapbox geocoding isn't configured on this server.")

        params = {
            "longitude": longitude,
            "latitude": latitude,
            "access_token": self._config.access_token,
            "country": self._config.country_bias,
            "permanent": "true" if self._config.permanent else "false",
            "limit": 1,
        }

        try:
            response = requests.get(_REVERSE_GEOCODE_URL, params=params, timeout=self._config.request_timeout_seconds)
        except requests.RequestException as exc:
            raise GeocodingProviderError(f"Couldn't reach Mapbox: {exc}") from exc

        if response.status_code != 200:
            raise GeocodingProviderError(f"Mapbox returned {response.status_code}: {response.text[:200]}")

        try:
            body = response.json()
            features = body.get("features", [])
            if not features:
                # A genuinely empty result -- no address data at this
                # point, not an error. Common enough for rural areas
                # that it's a normal, expected outcome, not a
                # failure the frontend needs to react to specially.
                return GeocodedAddress()

            context = features[0].get("properties", {}).get("context", {})
            return GeocodedAddress(
                street=context.get("street", {}).get("name"),
                suburb=context.get("neighborhood", {}).get("name"),
                city=context.get("place", {}).get("name"),
                province=context.get("region", {}).get("name"),
                postal_code=context.get("postcode", {}).get("name"),
            )
        except (ValueError, KeyError, AttributeError) as exc:
            # Mapbox's own response shape changed or is malformed --
            # this codebase's response contract (features[0].properties.context)
            # is real and confirmed against current docs, but treated
            # as fallible rather than assumed to hold forever.
            raise GeocodingProviderError(f"Couldn't parse Mapbox's response: {exc}") from exc

    def suggest(self, query: str, session_token: str, proximity: tuple | None = None):
        if not self._config.access_token:
            raise GeocodingProviderError("Mapbox geocoding isn't configured on this server.")

        params = {
            "q": query,
            "session_token": session_token,
            "access_token": self._config.access_token,
            "country": self._config.country_bias,
            "language": "en",
            "limit": 5,
        }
        if proximity is not None:
            # proximity arrives as (latitude, longitude) -- same order
            # as every other coordinate pair in this file
            # (reverse_geocode's params, retrieve's return value).
            # Converted to Mapbox's own required "longitude,latitude"
            # string ONLY here, at the point of building the actual
            # request -- never let Mapbox's convention leak backward
            # into this codebase's own internal ordering.
            latitude, longitude = proximity
            params["proximity"] = f"{longitude},{latitude}"

        try:
            response = requests.get(_SUGGEST_URL, params=params, timeout=self._config.request_timeout_seconds)
        except requests.RequestException as exc:
            raise GeocodingProviderError(f"Couldn't reach Mapbox: {exc}") from exc

        if response.status_code != 200:
            raise GeocodingProviderError(f"Mapbox returned {response.status_code}: {response.text[:200]}")

        try:
            body = response.json()
            return [
                SearchSuggestion(
                    mapbox_id=item["mapbox_id"],
                    name=item.get("name", ""),
                    full_address=item.get("full_address") or item.get("place_formatted"),
                )
                for item in body.get("suggestions", [])
            ]
        except (ValueError, KeyError, AttributeError) as exc:
            raise GeocodingProviderError(f"Couldn't parse Mapbox's response: {exc}") from exc

    def retrieve(self, mapbox_id: str, session_token: str) -> tuple:
        if not self._config.access_token:
            raise GeocodingProviderError("Mapbox geocoding isn't configured on this server.")

        params = {"session_token": session_token, "access_token": self._config.access_token}
        url = _RETRIEVE_URL_TEMPLATE.format(mapbox_id=mapbox_id)

        try:
            response = requests.get(url, params=params, timeout=self._config.request_timeout_seconds)
        except requests.RequestException as exc:
            raise GeocodingProviderError(f"Couldn't reach Mapbox: {exc}") from exc

        if response.status_code != 200:
            raise GeocodingProviderError(f"Mapbox returned {response.status_code}: {response.text[:200]}")

        try:
            body = response.json()
            features = body.get("features", [])
            if not features:
                raise GeocodingProviderError("Mapbox returned no location for that suggestion.")
            longitude, latitude = features[0]["geometry"]["coordinates"]
            return (float(latitude), float(longitude))
        except (ValueError, KeyError, AttributeError, IndexError) as exc:
            raise GeocodingProviderError(f"Couldn't parse Mapbox's response: {exc}") from exc
