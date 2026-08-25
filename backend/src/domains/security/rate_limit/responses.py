"""
The rate-limit-exceeded response handler.

DOMAIN-AGNOSTIC BY DESIGN: this module never imports a specific
domain's rate_limit/policies.py (previously it imported auth's
directly -- that coupling is exactly what this refactor removes).
Instead, each domain registers its own endpoint -> event mapping into _AUDIT_EVENT_REGISTRY via register_audit_events(), called
explicitly at app-boot time (see src/__init__.py's
_register_error_handlers). security/ owns the ENGINE; each domain owns
its own POLICY and registers into the shared engine -- the same
"registry a fresh app boot populates explicitly" idiom already used by
master_scheduler/registry.py and security/detection/registry.py, not a
new pattern invented for this file.

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
from typing import Optional

from flask import Flask, jsonify, request
from flask_jwt_extended import get_jwt_identity
from flask_limiter.errors import RateLimitExceeded

from src.shared.audit import audit as shared_audit
from src.shared.audit.audit_types import AuditEventNameType

logger = logging.getLogger(__name__)

# Populated by each domain's rate_limit/policies.py via
# register_audit_events(), called explicitly during app boot -- see
# src/__init__.py. Never populated by this module itself.
_AUDIT_EVENT_REGISTRY: dict[str, AuditEventNameType] = {}


def register_audit_events(mapping: dict[str, AuditEventNameType]) -> None:
    """Called once per domain at app-boot time, e.g.:

        from src.domains.auth.rate_limit.policies import RATE_LIMIT_AUDIT_EVENTS
        rate_limit_responses.register_audit_events(RATE_LIMIT_AUDIT_EVENTS)

    Merges rather than replaces, so multiple domains can each register
    their own mapping independently without needing to know about each
    other or coordinate a single combined dict themselves."""
    _AUDIT_EVENT_REGISTRY.update(mapping)


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
    register() below). Runs for EVERY route ANY domain's limiter guards
    -- Loan Book/Order Book/Business/Supplier adding their own limits
    later gets this same handler for free, with zero changes needed
    here, as long as they call register_audit_events() with their own
    mapping at boot time.

    Records the violation through the EXISTING shared.audit system --
    no new table, no duplicate audit infrastructure. Rate limiting
    enforces; shared.audit records. Auditing never blocks or fails the
    429 response: if audit logging itself throws, the response still
    goes out (publish() already never raises -- see shared/audit/audit.py
    -- and the call below is still wrapped as a second layer of safety
    specifically for this handler).
    """
    retry_after = _retry_after_seconds(error)
    event_name = _AUDIT_EVENT_REGISTRY.get(request.endpoint)

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
