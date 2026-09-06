"""
Formal test coverage for src/domains/network/geocoding, converted
from the same "manual proof first" discipline this codebase applies
everywhere else. No real network call to Mapbox is ever made here --
requests.get is monkeypatched at the mapbox_provider module level, the
same lightweight approach test_manual_checkout_works_with_zero_payfast_config
already uses for provider isolation (monkeypatch, not a mocking
framework -- none is a dependency of this project).
"""
from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token

from src.domains.network.geocoding.config.geocoding_config import GeocodingConfig
from src.domains.network.geocoding.errors import GeocodingProviderError
from src.domains.network.geocoding.providers import mapbox_provider as mapbox_provider_module
from src.domains.network.geocoding.providers.composition import get_geocoding_provider, reset_geocoding_provider
from src.domains.network.geocoding.providers.mapbox_provider import MapboxGeocodingProvider
from src.domains.network.geocoding.providers.provider import GeocodedAddress


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


_REAL_V6_CONTEXT_PAYLOAD = {
    "features": [
        {
            "properties": {
                "context": {
                    "street": {"name": "Lucky John Drive"},
                    "neighborhood": {"name": "Park Meadows"},
                    "place": {"name": "Park City"},
                    "region": {"name": "Utah"},
                    "postcode": {"name": "84060"},
                }
            }
        }
    ]
}


# --- MapboxGeocodingProvider -------------------------------------------------


def test_reverse_geocode_maps_context_fields_correctly(monkeypatch):
    """The real, confirmed v6 response shape (context.{type}.name) maps
    onto our own field names correctly -- this is the one piece of
    this whole feature genuinely tied to Mapbox's own documented
    contract, so it's worth pinning down exactly."""
    monkeypatch.setattr(
        mapbox_provider_module.requests, "get", lambda url, params, timeout: _FakeResponse(200, _REAL_V6_CONTEXT_PAYLOAD)
    )
    provider = MapboxGeocodingProvider(GeocodingConfig(access_token="fake-token"))

    address = provider.reverse_geocode(40.725163, -111.86313)

    assert address.street == "Lucky John Drive"
    assert address.suburb == "Park Meadows"
    assert address.city == "Park City"
    assert address.province == "Utah"
    assert address.postal_code == "84060"
    # Mapbox has no such concept -- always left for the business to
    # fill in themselves, never populated by any provider.
    assert address.building is None


def test_reverse_geocode_returns_empty_result_for_no_features(monkeypatch):
    """A genuinely empty match (e.g. an informal/rural pin Mapbox's
    data doesn't cover) is a normal, valid outcome -- not an error the
    caller needs to handle specially. See GeocodingProvider's own
    docstring."""
    monkeypatch.setattr(
        mapbox_provider_module.requests, "get", lambda url, params, timeout: _FakeResponse(200, {"features": []})
    )
    provider = MapboxGeocodingProvider(GeocodingConfig(access_token="fake-token"))

    address = provider.reverse_geocode(-23.9045, 29.4587)

    assert address == GeocodedAddress()


def test_reverse_geocode_raises_on_non_200(monkeypatch):
    monkeypatch.setattr(
        mapbox_provider_module.requests,
        "get",
        lambda url, params, timeout: _FakeResponse(401, text="Not Authorized - Invalid Token"),
    )
    provider = MapboxGeocodingProvider(GeocodingConfig(access_token="bad-token"))

    with pytest.raises(GeocodingProviderError):
        provider.reverse_geocode(0.0, 0.0)


def test_reverse_geocode_raises_on_network_error(monkeypatch):
    import requests as requests_lib

    def _raise(*args, **kwargs):
        raise requests_lib.ConnectionError("no route to host")

    monkeypatch.setattr(mapbox_provider_module.requests, "get", _raise)
    provider = MapboxGeocodingProvider(GeocodingConfig(access_token="fake-token"))

    with pytest.raises(GeocodingProviderError):
        provider.reverse_geocode(0.0, 0.0)


def test_reverse_geocode_raises_when_token_missing():
    """A missing token is a real deployment problem, distinct from a
    genuine no-match lookup -- must never silently return an empty
    GeocodedAddress that looks like a valid rural-area result."""
    provider = MapboxGeocodingProvider(GeocodingConfig(access_token=""))

    with pytest.raises(GeocodingProviderError):
        provider.reverse_geocode(0.0, 0.0)


def test_permanent_flag_is_passed_through_as_configured(monkeypatch):
    """GeocodingConfig.permanent actually reaches the real request --
    this is the one flag standing between the free, temporary tier
    this feature is designed around and Mapbox's paid permanent tier
    (see GeocodingConfig's own docstring)."""
    captured_params = {}

    def _fake_get(url, params, timeout):
        captured_params.update(params)
        return _FakeResponse(200, {"features": []})

    monkeypatch.setattr(mapbox_provider_module.requests, "get", _fake_get)

    MapboxGeocodingProvider(GeocodingConfig(access_token="fake-token", permanent=False)).reverse_geocode(0.0, 0.0)
    assert captured_params["permanent"] == "false"

    MapboxGeocodingProvider(GeocodingConfig(access_token="fake-token", permanent=True)).reverse_geocode(0.0, 0.0)
    assert captured_params["permanent"] == "true"


# --- composition -------------------------------------------------------------


def test_get_geocoding_provider_returns_a_real_mapbox_provider(monkeypatch):
    reset_geocoding_provider()
    monkeypatch.setenv("MAPBOX_BACKEND_TOKEN", "fake-token")

    provider = get_geocoding_provider()

    assert isinstance(provider, MapboxGeocodingProvider)
    reset_geocoding_provider()


# --- HTTP route ----------------------------------------------------------------


def test_reverse_geocode_route_requires_authentication(client):
    response = client.get("/api/v1/geocoding/reverse?latitude=-23.9&longitude=29.4")
    assert response.status_code == 401


def test_reverse_geocode_route_rejects_missing_coordinates(client, make_user, db_session):
    from src.domains.auth.models.user import UserRole, VerificationStatus

    user = make_user("business@example.com", role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED)
    db_session.commit()

    response = client.get(
        "/api/v1/geocoding/reverse", headers={"Authorization": f"Bearer {_token_for(user, 'business')}"}
    )

    assert response.status_code == 422


def test_reverse_geocode_route_rejects_out_of_range_coordinates(client, make_user, db_session):
    from src.domains.auth.models.user import UserRole, VerificationStatus

    user = make_user("business2@example.com", role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED)
    db_session.commit()

    response = client.get(
        "/api/v1/geocoding/reverse?latitude=999&longitude=29.4",
        headers={"Authorization": f"Bearer {_token_for(user, 'business')}"},
    )

    assert response.status_code == 422


def test_reverse_geocode_route_returns_mapped_address(client, make_user, db_session, monkeypatch):
    from src.domains.auth.models.user import UserRole, VerificationStatus

    user = make_user("business3@example.com", role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED)
    db_session.commit()

    monkeypatch.setattr(
        mapbox_provider_module.requests, "get", lambda url, params, timeout: _FakeResponse(200, _REAL_V6_CONTEXT_PAYLOAD)
    )
    reset_geocoding_provider()
    monkeypatch.setenv("MAPBOX_BACKEND_TOKEN", "fake-token")

    response = client.get(
        "/api/v1/geocoding/reverse?latitude=40.725163&longitude=-111.86313",
        headers={"Authorization": f"Bearer {_token_for(user, 'business')}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["street"] == "Lucky John Drive"
    assert data["suburb"] == "Park Meadows"
    assert data["postalCode"] == "84060"
    reset_geocoding_provider()


def test_reverse_geocode_route_is_genuinely_role_agnostic(client, make_user, db_session, monkeypatch):
    """THE REAL POINT of this route's auth design -- confirms a
    SUPPLIER token works here too, not just business, since a future
    supplier-own-pin feature depends on that being true (see
    geocoding_routes.py's own docstring). Deliberately no
    @role_required anywhere on this blueprint."""
    from src.domains.auth.models.user import UserRole, VerificationStatus

    supplier_user = make_user(
        "supplier@example.com", role=UserRole.SUPPLIER, verification_status=VerificationStatus.VERIFIED
    )
    db_session.commit()

    monkeypatch.setattr(
        mapbox_provider_module.requests, "get", lambda url, params, timeout: _FakeResponse(200, {"features": []})
    )
    reset_geocoding_provider()
    monkeypatch.setenv("MAPBOX_BACKEND_TOKEN", "fake-token")

    response = client.get(
        "/api/v1/geocoding/reverse?latitude=0&longitude=0",
        headers={"Authorization": f"Bearer {_token_for(supplier_user, 'supplier')}"},
    )

    assert response.status_code == 200
    reset_geocoding_provider()


# --- Search Box API: suggest / retrieve --------------------------------------

_SUGGEST_PAYLOAD = {
    "suggestions": [
        {"mapbox_id": "abc123", "name": "University Road", "full_address": "University Road, Mankweng, Limpopo"},
        {"mapbox_id": "def456", "name": "University of the North", "place_formatted": "Mankweng, Limpopo"},
    ]
}

_RETRIEVE_PAYLOAD = {"features": [{"geometry": {"type": "Point", "coordinates": [29.454, -23.910]}}]}


def test_suggest_maps_suggestions_correctly(monkeypatch):
    monkeypatch.setattr(mapbox_provider_module.requests, "get", lambda url, params, timeout: _FakeResponse(200, _SUGGEST_PAYLOAD))
    provider = MapboxGeocodingProvider(GeocodingConfig(access_token="fake-token"))

    results = provider.suggest("university", "session-1")

    assert len(results) == 2
    assert results[0].mapbox_id == "abc123"
    assert results[0].name == "University Road"
    assert results[0].full_address == "University Road, Mankweng, Limpopo"
    # place_formatted used as a fallback when full_address is absent --
    # Search Box's two possible field names for the secondary line.
    assert results[1].full_address == "Mankweng, Limpopo"


def test_suggest_includes_proximity_when_given(monkeypatch):
    captured_params = {}

    def _fake_get(url, params, timeout):
        captured_params.update(params)
        return _FakeResponse(200, {"suggestions": []})

    monkeypatch.setattr(mapbox_provider_module.requests, "get", _fake_get)
    provider = MapboxGeocodingProvider(GeocodingConfig(access_token="fake-token"))

    provider.suggest("church street", "session-1", proximity=(-23.91, 29.45))

    # Mapbox's own convention: longitude,latitude -- confirmed to
    # match how every other coordinate pair in this provider is sent.
    assert captured_params["proximity"] == "29.45,-23.91"


def test_retrieve_returns_coordinates_only(monkeypatch):
    monkeypatch.setattr(mapbox_provider_module.requests, "get", lambda url, params, timeout: _FakeResponse(200, _RETRIEVE_PAYLOAD))
    provider = MapboxGeocodingProvider(GeocodingConfig(access_token="fake-token"))

    latitude, longitude = provider.retrieve("abc123", "session-1")

    assert latitude == pytest.approx(-23.910)
    assert longitude == pytest.approx(29.454)


def test_retrieve_raises_on_empty_features(monkeypatch):
    monkeypatch.setattr(mapbox_provider_module.requests, "get", lambda url, params, timeout: _FakeResponse(200, {"features": []}))
    provider = MapboxGeocodingProvider(GeocodingConfig(access_token="fake-token"))

    with pytest.raises(GeocodingProviderError):
        provider.retrieve("abc123", "session-1")


def test_search_suggest_route_requires_session_token(client, make_user, db_session):
    from src.domains.auth.models.user import UserRole, VerificationStatus

    user = make_user("search1@example.com", role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED)
    db_session.commit()

    response = client.get(
        "/api/v1/geocoding/search?q=university", headers={"Authorization": f"Bearer {_token_for(user, 'business')}"}
    )

    assert response.status_code == 422


def test_search_suggest_route_returns_mapped_suggestions(client, make_user, db_session, monkeypatch):
    from src.domains.auth.models.user import UserRole, VerificationStatus

    user = make_user("search2@example.com", role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED)
    db_session.commit()

    monkeypatch.setattr(mapbox_provider_module.requests, "get", lambda url, params, timeout: _FakeResponse(200, _SUGGEST_PAYLOAD))
    reset_geocoding_provider()
    monkeypatch.setenv("MAPBOX_BACKEND_TOKEN", "fake-token")

    response = client.get(
        "/api/v1/geocoding/search?q=university&session_token=session-1",
        headers={"Authorization": f"Bearer {_token_for(user, 'business')}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 2
    assert data[0]["mapboxId"] == "abc123"
    reset_geocoding_provider()


def test_search_retrieve_route_returns_coordinates(client, make_user, db_session, monkeypatch):
    from src.domains.auth.models.user import UserRole, VerificationStatus

    user = make_user("search3@example.com", role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED)
    db_session.commit()

    monkeypatch.setattr(mapbox_provider_module.requests, "get", lambda url, params, timeout: _FakeResponse(200, _RETRIEVE_PAYLOAD))
    reset_geocoding_provider()
    monkeypatch.setenv("MAPBOX_BACKEND_TOKEN", "fake-token")

    response = client.get(
        "/api/v1/geocoding/search/retrieve?mapbox_id=abc123&session_token=session-1",
        headers={"Authorization": f"Bearer {_token_for(user, 'business')}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["latitude"] == pytest.approx(-23.910)
    assert data["longitude"] == pytest.approx(29.454)
    reset_geocoding_provider()
