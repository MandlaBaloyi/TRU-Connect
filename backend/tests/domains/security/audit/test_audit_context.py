"""
Request-context enrichment — with and without a live request.

The "without" half matters as much as the "with": audit events are
published from the scheduler, from tests, and (later) from CLI commands,
none of which have a request.
"""

from __future__ import annotations

import pytest
from flask import Flask

from src.shared import audit, audit_context
from src.shared.audit_types import AuditEventName


@pytest.fixture()
def app():
    return Flask(__name__)


@pytest.fixture(autouse=True)
def _isolate_listeners():
    original = audit._listeners[:]
    audit._listeners.clear()
    yield
    audit._listeners[:] = original


def test_context_getters_return_none_outside_request():
    assert audit_context.get_ip_address() is None
    assert audit_context.get_user_agent() is None
    assert audit_context.get_correlation_id() is None
    assert audit_context.get_endpoint() is None
    assert audit_context.get_http_method() is None
    assert audit_context.get_device_id() is None


def test_enriches_from_live_request(app):
    received = []
    audit.register_listener(received.append)

    with app.test_request_context(
        "/api/v1/auth/login",
        method="POST",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/120"},
        environ_base={"REMOTE_ADDR": "198.51.100.7"},
    ):
        audit.log_login_failed(email="a@example.com", ip_address=None)

    event = received[0]
    assert event.ip_address == "198.51.100.7"
    assert event.endpoint == "/api/v1/auth/login"
    assert event.http_method == "POST"
    assert event.browser == "Chrome"
    assert event.operating_system == "Windows"
    assert event.platform == "web"
    assert event.correlation_id is not None


def test_x_forwarded_for_takes_precedence(app):
    """Behind a proxy, remote_addr is the proxy — useless for investigation."""
    with app.test_request_context(
        "/x",
        headers={"X-Forwarded-For": "203.0.113.5, 10.0.0.1"},
        environ_base={"REMOTE_ADDR": "10.0.0.1"},
    ):
        assert audit_context.get_ip_address() == "203.0.113.5"


def test_correlation_id_is_stable_within_one_request(app):
    """Multi-step flows must share one correlation id to stitch together."""
    received = []
    audit.register_listener(received.append)

    with app.test_request_context("/api/v1/auth/register"):
        audit.log_otp_created(user_id="u1", email="a@example.com")
        audit.log_otp_verified(user_id="u1", email="a@example.com")

    assert received[0].correlation_id == received[1].correlation_id


def test_inbound_correlation_header_is_honoured(app):
    with app.test_request_context("/x", headers={"X-Correlation-ID": "client-trace-42"}):
        assert audit_context.get_correlation_id() == "client-trace-42"


@pytest.mark.parametrize("ua,browser,os_name,platform", [
    ("Mozilla/5.0 (Windows NT 10.0) Chrome/120", "Chrome", "Windows", "web"),
    ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Safari/604", "Safari", "iOS", "mobile"),
    ("okhttp/4.9.0", "Mobile App", None, "mobile"),
    (None, None, None, None),
])
def test_user_agent_parsing(ua, browser, os_name, platform):
    assert audit_context.parse_user_agent(ua) == (browser, os_name, platform)


@pytest.mark.parametrize("ua,browser,os_name,platform", [
    # Real-world React Native / Expo native-client UAs, which never
    # contain the browser-style "android"/"iphone" markers — this is
    # what a physical device test against this file actually sends.
    ("Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TQ3A.230901.001)", "Mobile App", "Android", "mobile"),
    ("MyApp/1 CFNetwork/1240.0.4 Darwin/20.6.0", "Mobile App", "iOS", "mobile"),
    ("Expo/2.30.0 CFNetwork/1240 Darwin/20", "Mobile App", "iOS", "mobile"),
])
def test_native_app_user_agent_parsing(ua, browser, os_name, platform):
    assert audit_context.parse_user_agent(ua) == (browser, os_name, platform)
