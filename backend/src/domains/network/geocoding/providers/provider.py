"""
GeocodingProvider -- the abstract contract every geocoding vendor
implements. geocoding_routes.py depends on THIS interface, never on
mapbox_provider.py or the Mapbox HTTP API directly -- same isolation
shape as orders/providers/provider.py (PayFast swappable behind
PaymentProvider) and shared/media/providers/provider.py (Cloudinary
swappable behind MediaProvider), deliberately mirrored rather than
invented fresh. One abstraction, one real implementation today
(Mapbox), one place (composition.py) that would need to change if a
future implementation (e.g. Google Places, if the cash-flow picture
changes) ever replaced it -- no route or service code would need to.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GeocodedAddress:
    """What a reverse-geocode lookup hands back -- deliberately just the
    address TEXT components, never the provider's raw response object,
    never coordinates. The pin's own lat/lng already lives in the
    frontend (it's what the business dragged the map to); echoing it
    back here would only invite a caller to trust the provider's
    number over the map's own truth. Every field is optional: Mapbox's
    real-world South African coverage is untested for rural/informal
    addresses (see GeocodingProvider's own module docstring), so a
    lookup that only manages a city and province, or returns nothing
    useful at all, must still be a valid, non-error result -- the
    business always has final say via the editable fields on screen.

    `building` is deliberately never populated by any provider --
    Mapbox has no such field (a spaza's own building/landmark
    description is something only the business itself can supply) --
    kept here only so the frontend's address-fields shape stays
    consistent whether it came from a lookup or was typed by hand.
    """

    building: Optional[str] = None
    street: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None


@dataclass(frozen=True)
class SearchSuggestion:
    """One typeahead result from the Search Box API's /suggest step --
    just enough to show a picker list and to pass back into retrieve()
    once tapped. Never the full Search Box response object (extra
    fields like category/maki/distance aren't used here and aren't
    worth a caller depending on)."""

    mapbox_id: str
    name: str
    full_address: Optional[str]


class GeocodingProvider(ABC):
    @abstractmethod
    def reverse_geocode(self, latitude: float, longitude: float) -> GeocodedAddress:
        """Given a pin's real coordinates (already chosen by the user on
        the map, never produced by this method), returns this
        provider's best guess at the address there, for pre-filling
        editable form fields. Never raises for "no good match found"
        -- an empty-but-valid GeocodedAddress is a normal, expected
        result for a rural/informal address a provider's data doesn't
        cover well; only raises GeocodingProviderError for a genuine
        transport/parsing failure (see that error's own docstring)."""

    @abstractmethod
    def suggest(
        self, query: str, session_token: str, proximity: Optional[tuple[float, float]] = None
    ) -> list["SearchSuggestion"]:
        """Part one of the Search Box API's two-step interactive search
        -- typeahead suggestions as the business types a street/place
        name. session_token MUST be reused across every suggest call
        AND the one retrieve call that completes this search, and
        never reused across a different, later search -- this is what
        Mapbox bills a whole search as ONE session on, not per
        keystroke. proximity, when given, is (latitude, longitude) --
        same order as reverse_geocode's own params and retrieve's own
        return value below, deliberately consistent across this whole
        interface even though Mapbox's actual wire format wants
        longitude first (implementations convert at the point of the
        real HTTP call, never before -- see mapbox_provider.py, where
        an earlier version of this got the order backwards and a real
        test caught it). Biases results toward wherever the map is
        currently centered, for better local relevance. Returns an
        empty list for "no matches", never raises for that -- same
        "no match is a normal outcome" reasoning as reverse_geocode
        above."""

    @abstractmethod
    def retrieve(self, mapbox_id: str, session_token: str) -> tuple[float, float]:
        """Part two -- given a suggestion the business actually tapped,
        resolves it to real coordinates (latitude, longitude). MUST
        pass the SAME session_token used for the suggest calls that
        produced this mapbox_id, completing that billing session.
        This is the ONLY thing this method returns -- deliberately not
        the address text Search Box's own retrieve response also
        contains (see mapbox_provider.py's own docstring for why:
        one single source of address-field truth, reverse_geocode,
        rather than two different response shapes populating the same
        fields two different ways)."""
