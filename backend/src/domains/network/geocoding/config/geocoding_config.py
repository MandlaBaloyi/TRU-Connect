"""
GeocodingConfig -- ONLY what's genuinely universal to every reverse-
geocode lookup this backend makes: the Mapbox token, a default country
bias, and the temporary/permanent switch. Same "only what's really
shared, nothing here is a business rule" discipline as MediaConfig and
PaymentConfig.

WHY `permanent` LIVES HERE, NOT HARDCODED IN THE PROVIDER: Mapbox's
Geocoding API defaults every request to *temporary* -- results may be
shown to a user in real time but not cached or stored -- unless the
caller explicitly passes permanent=true, which requires a card on file
and is billed per request with no free allowance at all (confirmed
directly against Mapbox's own API docs, not assumed). TruConnect's
actual design never stores Mapbox's own response: the pin's real
lat/lng comes straight off the map widget the user dragged (never a
geocoding call at all), and the address text saved to the order is
whatever the business confirmed/edited on screen, not the raw API
payload. That keeps every call this backend makes squarely inside the
free, temporary tier by design -- but if that ever needs to change
(e.g. wanting a fully unambiguous storage licence once there's real
revenue), it's this ONE flag, not a rewrite. See mapbox_provider.py's
own docstring for how the flag is actually used.

WHY country DEFAULTS TO "za": every real user of this app is a South
African informal business or supplier -- biasing every lookup to South
Africa measurably improves match quality for ambiguous village/town
names (e.g. "Elim" exists in multiple countries) and costs nothing to
set. Still overridable per-request if that's ever needed (e.g. a
future cross-border supplier), never hardcoded past this default.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GeocodingConfig:
    access_token: str
    country_bias: str = "za"
    permanent: bool = False
    # Mapbox's own default rate limit is 1000 requests/minute per
    # account -- this is a per-CALL network timeout, a different
    # concern entirely: how long this backend waits on a single slow
    # request before giving up and telling the frontend to let the
    # business fill the fields in by hand. Generous enough for a slow
    # rural connection, short enough that a Flask request thread never
    # hangs indefinitely on a third party being down.
    request_timeout_seconds: float = 5.0

    @classmethod
    def from_env(cls) -> "GeocodingConfig":
        return cls(
            access_token=os.environ.get("MAPBOX_BACKEND_TOKEN", ""),
            country_bias=os.environ.get("MAPBOX_COUNTRY_BIAS", "za"),
            permanent=os.environ.get("MAPBOX_PERMANENT_GEOCODING", "false").lower() == "true",
        )
