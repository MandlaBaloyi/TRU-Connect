"""
get_geocoding_provider() -- the ONE place in this codebase that
decides which provider handles a reverse-geocode lookup. Every caller
calls this function, never `MapboxGeocodingProvider(...)` directly --
same discipline as orders/providers/composition.py's own
get_payment_provider and shared/media/providers/composition.py's own
get_media_provider.
"""
from __future__ import annotations

from src.domains.network.geocoding.config.geocoding_config import GeocodingConfig
from src.domains.network.geocoding.providers.provider import GeocodingProvider

_mapbox_provider: GeocodingProvider | None = None


def get_geocoding_provider() -> GeocodingProvider:
    global _mapbox_provider

    if _mapbox_provider is None:
        from src.domains.network.geocoding.providers.mapbox_provider import MapboxGeocodingProvider

        _mapbox_provider = MapboxGeocodingProvider(GeocodingConfig.from_env())
    return _mapbox_provider


def reset_geocoding_provider() -> None:
    """Test-only -- lets each test start from a clean provider instance
    rather than one memoized across the whole test session, same
    reasoning as shared/media's own reset_media_provider."""
    global _mapbox_provider
    _mapbox_provider = None
