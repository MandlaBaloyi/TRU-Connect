"""
The rate-limit-exceeded response handler.

RESPONSE SHAPE IS A DELIBERATE, APPROVED EXCEPTION to this project's
general {"success": false, "message": ..., "errors": [], "code": ...}
envelope (see src/core/responses.py). The shape below --
{"error": "rate_limit_exceeded", "message": ..., "retry_after": N} --
was explicitly specified and approved for Phase 1. Noted here so a
future maintainer doesn't "fix" it back to the general envelope without
knowing that was a deliberate choice, not a miss.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from flask import Flask, jsonify, request
from flask_jwt_extended import get_jwt_identity
from flask_limiter.errors import RateLimitExceeded

from src.domains.security.rate_limit.policies import RATE_LIMIT_AUDIT_EVENTS
from src.shared.audit import audit as shared_audit

logger = logging.getLogger(__name__)


def _current_email() -> Optional[str]:
    """Best-effort only -- not every rate-limited route's body has an
    'email' field (e.g. reset-password uses a ticket), and the body may
    not be valid JSON at all if that's WHY the request looked abusive.
    Never raises either way."""
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    return email.strip().lower() if isinstance(email, str) and email.strip() else None


def _current_user_id() -> Optional[str]:
    """Almost always None -- see log_rate_limit_exceeded's docstring in
    shared/audit/audit.py for why the limiter running BEFORE
    authentication means there is usually no verified identity yet at
    this point. Never raises: get_jwt_identity() outside a valid JWT
    context raises, which this call site is exactly the risk of."""
    try:
        return get_jwt_identity()
    except Exception:  # noqa: BLE001
        return None


def _retry_after_seconds(error: RateLimitExceeded) -> int:
    """The configured window length for the limit that was hit (e.g. 60
    for "5 per minute"), NOT the precise remaining time within the
    current window -- computing the exact remaining time would mean
    querying the storage backend's internal state, which is more
    fragile and not worth it for a Phase 1 value the frontend is only
    meant to show as an approximate "try again in about a minute"
    message. Verified against the real installed flask-limiter/limits
    API (RuntimeLimit.limit is a limits.RateLimitItem, which exposes
    get_expiry() publicly) rather than guessed."""
    return error.limit.limit.get_expiry()


def handle_rate_limit_exceeded(error: RateLimitExceeded):
    """
    Registered as the Flask error handler for RateLimitExceeded (see
    register() below). Runs for EVERY route the limiter guards, Auth or
    otherwise -- Phase 2/3 adding Loan Book/Order Book limits gets this
    same handler for free.

    Records the violation through the EXISTING shared.audit system --
    no new table, no duplicate audit infrastructure. Rate limiting
    enforces; shared.audit records. Auditing never blocks or fails the
    429 response: if audit logging itself throws, the response still
    goes out (publish() already never raises -- see shared/audit/audit.py
    -- and the call below is still wrapped as a second layer of safety
    specifically for this handler).
    """
    retry_after = _retry_after_seconds(error)
    event_name = RATE_LIMIT_AUDIT_EVENTS.get(request.endpoint)

    if event_name is not None:
        try:
            shared_audit.log_rate_limit_exceeded(
                event_name,
                ip_address=request.remote_addr,
                email=_current_email(),
                user_id=_current_user_id(),
                endpoint=request.endpoint,
                http_method=request.method,
                metadata={"policy": str(error.limit.limit), "retry_after_seconds": retry_after},
            )
        except Exception:  # noqa: BLE001 -- see docstring: auditing must never break the 429 response
            logger.exception("failed to record rate-limit audit event for endpoint=%s", request.endpoint)

    response = jsonify({
        "error": "rate_limit_exceeded",
        "message": "Too many requests. Please try again later.",
        "retry_after": retry_after,
    })
    response.status_code = 429
    response.headers["Retry-After"] = str(retry_after)
    return response


def register(app: Flask) -> None:
    """Wires the handler into the app -- called once from create_app(),
    same call shape as audit_service.register(app)."""
    app.register_error_handler(RateLimitExceeded, handle_rate_limit_exceeded)
