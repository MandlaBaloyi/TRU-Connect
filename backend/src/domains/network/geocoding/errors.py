"""
domains.network.geocoding exceptions -- real src.core.exceptions.AppError
subclasses, same convention as every other domain in this codebase. Routes
never catch these directly; the app factory's single AppError handler
(src/__init__.py) converts them into the standard JSON envelope.
"""
from __future__ import annotations

from src.core.exceptions import AppError


class GeocodingProviderError(AppError):
    """Raised when Mapbox itself can't be reached, times out, or returns
    something this backend can't parse -- deliberately 502 (Bad Gateway),
    not 400/422: the business's request was fine, an upstream service
    failed. The frontend's own useReverseGeocode hook treats this as
    "let the person fill the address fields in by hand" rather than a
    hard failure -- a map pin the business already dropped is still
    saved either way; only the auto-fill convenience is lost."""

    status_code = 502
    code = "GEOCODING_PROVIDER_ERROR"
