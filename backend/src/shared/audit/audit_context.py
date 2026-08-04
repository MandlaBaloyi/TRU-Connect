"""
Automatic request-context enrichment for audit events.

WHY THIS EXISTS: the audit model wants IP, user agent, endpoint, HTTP
method, correlation ID, etc. Threading all of those through every
service-layer function signature would mean touching every call site in
auth_service.py / otp_service.py / password_reset_service.py — and would
mean every FUTURE domain has to remember to pass them too. Instead this
module pulls them from Flask's request context automatically, so
publishers only supply what they actually know (user id, email, outcome).

CRITICAL PROPERTY — must degrade gracefully with no request context.
Audit events are published from at least three places with no HTTP
request at all:
    - the scheduled cleanup job (background thread, app context only)
    - future CLI/management commands
    - tests calling services directly
Every function here returns None rather than raising when there is no
request. A background job that crashes at 3am because the audit layer
assumed a request object would be a self-inflicted outage.
"""

from __future__ import annotations

import uuid
from typing import Optional

from flask import g, has_request_context, request

CORRELATION_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"


def get_correlation_id() -> Optional[str]:
    """
    Stable ID for one logical flow. Read from an inbound header if the
    caller supplied one (lets a mobile client tie its own trace to
    server-side events), otherwise generated once per request and cached
    on `g` so every event in that request shares it.

    Returns None outside a request context — a scheduled job has no
    correlation to speak of.
    """
    if not has_request_context():
        return None
    if not hasattr(g, "_audit_correlation_id"):
        incoming = request.headers.get(CORRELATION_HEADER)
        g._audit_correlation_id = incoming or str(uuid.uuid4())
    return g._audit_correlation_id


def get_request_id() -> Optional[str]:
    if not has_request_context():
        return None
    if not hasattr(g, "_audit_request_id"):
        incoming = request.headers.get(REQUEST_ID_HEADER)
        g._audit_request_id = incoming or str(uuid.uuid4())
    return g._audit_request_id


def get_ip_address() -> Optional[str]:
    """
    Client IP, honouring X-Forwarded-For since this will sit behind a
    proxy/load balancer in production (where request.remote_addr would
    otherwise be the proxy's own address, making every audit row useless
    for investigation).

    NOTE: X-Forwarded-For is client-supplied and therefore spoofable. It
    is trusted here because the value is used for investigation and
    display, not for authorization decisions. If it ever becomes an input
    to a security control (e.g. IP allow-listing), configure Werkzeug's
    ProxyFix with an explicit trusted-proxy count instead of reading the
    header directly.
    """
    if not has_request_context():
        return None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def get_user_agent() -> Optional[str]:
    if not has_request_context():
        return None
    return request.headers.get("User-Agent")


def get_endpoint() -> Optional[str]:
    if not has_request_context():
        return None
    return request.path


def get_http_method() -> Optional[str]:
    if not has_request_context():
        return None
    return request.method


def get_device_id() -> Optional[str]:
    """Mobile clients may send a stable device identifier. Optional — the
    header simply won't be present for web/browser callers."""
    if not has_request_context():
        return None
    return request.headers.get("X-Device-ID")


def parse_user_agent(user_agent: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Best-effort (browser, os, platform) from a User-Agent string.

    Deliberately a crude substring check rather than a dependency on a
    UA-parsing library: these fields are display conveniences for the
    admin panel, not security controls, and a wrong guess is harmless.
    If richer device analytics ever matter, swap in a real parser here —
    this is the only place that would change.

    MOBILE-APP OS DETECTION — React Native / Expo's built-in fetch/XHR
    does NOT send a browser-style UA containing literal "android" or
    "ios". Its underlying native HTTP client sends its OWN platform
    signature instead:
        Android (OkHttp)  -> contains "okhttp" and often "dalvik"/"linux"
                              but rarely the word "android" itself
        iOS (CFNetwork)   -> contains "cfnetwork" and/or "darwin",
                              never the word "ios" or "iphone"
    A plain browser-style check (looking only for "android"/"iphone")
    correctly identifies "this is a mobile app" via the okhttp/expo
    check above, but then falls through on OS — which is exactly the
    null operating_system/platform observed in real device testing.
    Checked for explicitly below, ordered before the generic checks.
    """
    if not user_agent:
        return None, None, None

    ua = user_agent.lower()

    if "edg/" in ua:
        browser = "Edge"
    elif "chrome" in ua and "chromium" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "okhttp" in ua or "expo" in ua or "dalvik" in ua or "cfnetwork" in ua:
        browser = "Mobile App"
    else:
        browser = None

    # React Native / native-client signatures checked first — these UAs
    # never contain the browser-style "android"/"iphone" markers below.
    if "cfnetwork" in ua or "darwin" in ua:
        operating_system = "iOS"
    elif "dalvik" in ua or ("okhttp" in ua and "android" not in ua and "linux" in ua):
        operating_system = "Android"
    elif "windows" in ua:
        operating_system = "Windows"
    elif "android" in ua:
        operating_system = "Android"
    elif "iphone" in ua or "ipad" in ua or "ios" in ua:
        operating_system = "iOS"
    elif "mac os" in ua or "macintosh" in ua:
        operating_system = "macOS"
    elif "linux" in ua:
        operating_system = "Linux"
    else:
        operating_system = None

    if operating_system in ("Android", "iOS"):
        platform = "mobile"
    elif operating_system in ("Windows", "macOS", "Linux"):
        platform = "web"
    elif browser == "Mobile App":
        # We know it's a native app but couldn't pin the exact OS from
        # this particular UA string — still worth recording that it's
        # mobile rather than leaving platform null.
        platform = "mobile"
    else:
        platform = None

    return browser, operating_system, platform
