"""
Security's audit service -- subscribes to shared.audit and persists
events. Relocated from security/services/ to security/audit/services/.

============================================================
 THE APP-CONTEXT BUG, FIXED HERE
============================================================
ORIGINAL SYMPTOM: every ASYNC-classified event (OTP created, token
created, most of the high-volume events) silently failed to persist,
logging "RuntimeError: Working outside of application context".

ROOT CAUSE: _write_async() handed a deferred callable to
shared.queue.enqueue(), which runs it on a DIFFERENT THREAD, AFTER the
original Flask request has already finished. db.session is
Flask-SQLAlchemy's scoped session -- it needs an ACTIVE app context to
know which app's session to use, and by the time the background worker
picks up the job, that context is long gone. This is the exact same
class of problem the Master Scheduler's trigger.py already solved for
scheduled jobs (wrapping each tick in app.app_context()) -- this fix
applies that identical pattern here.

THE FIX: register(app) now takes the real Flask app instance explicitly
(same shape as master_scheduler.trigger.start(app)) and captures it in a
closure. Every deferred (ASYNC) write is wrapped in `app.app_context()`
at the point it actually executes, regardless of which thread that turns
out to be -- so it no longer matters whether shared.queue's worker
thread happens to preserve Flask's context or not; this file no longer
depends on that.
"""

from __future__ import annotations

import logging
from typing import Optional

from flask import Flask

from src.domains.security.audit.models.audit_event import AuditEventRecord
from src.domains.security.audit.repositories.audit_repository import AuditRepository
from src.domains.security.audit.rules.event_config import WriteMode, get_policy
from src.shared.audit import audit
from src.shared.audit.audit_types import AuditEvent

logger = logging.getLogger(__name__)

_registered = False


def to_record(event: AuditEvent) -> AuditEventRecord:
    policy = get_policy(event.event_name)
    category = event.category.value if event.category else policy.category.value
    severity = event.severity.value if event.severity else policy.severity.value

    return AuditEventRecord(
        timestamp=event.timestamp,
        domain=event.domain.value,
        module=event.module,
        event_name=event.event_name.value,
        category=category,
        severity=severity,
        status=event.status.value,
        failure_reason=event.failure_reason,
        actor_type=event.actor_type.value,
        user_id=event.user_id,
        email=event.email,
        role=event.role,
        tenant_id=event.tenant_id,
        ip_address=event.ip_address,
        user_agent=event.user_agent,
        browser=event.browser,
        operating_system=event.operating_system,
        platform=event.platform,
        device_id=event.device_id,
        session_id=event.session_id,
        correlation_id=event.correlation_id,
        request_id=event.request_id,
        http_method=event.http_method,
        endpoint=event.endpoint,
        http_status_code=event.http_status_code,
        event_metadata=event.metadata or {},
    )


def _write_now(event: AuditEvent) -> None:
    """Synchronous persist. Assumes an active app context already exists
    -- true for SYNC events (still inside the original request) and true
    for ASYNC events too, since _write_async() below wraps this call in
    one explicitly before ever invoking it."""
    try:
        AuditRepository.insert(to_record(event))
    except Exception:  # noqa: BLE001 -- auditing must never break the audited action
        logger.exception("failed to persist audit event=%s", event.event_name.value)


def _write_async(event: AuditEvent, app: Flask) -> None:
    """
    THE FIX: the deferred callable handed to the queue wraps _write_now()
    in `app.app_context()` itself -- it no longer trusts the queue's
    worker thread to have (or preserve) Flask's request context, because
    it demonstrably doesn't. `app` is captured via closure from
    register(app), the same pattern master_scheduler.trigger.py already
    uses for exactly the same class of problem.
    """

    def _deferred() -> None:
        with app.app_context():
            _write_now(event)

    try:
        from src.shared.queue.queue import enqueue

        enqueue(_deferred)
    except Exception:  # noqa: BLE001
        logger.warning(
            "audit queue unavailable for event=%s, falling back to synchronous write",
            event.event_name.value,
        )
        _write_now(event)


def register(app: Flask) -> None:
    """
    Subscribe to shared.audit. Called once at application startup (see
    the integration notes) -- REQUIRES the real Flask app instance now,
    unlike before, specifically so ASYNC writes can be wrapped in a real
    app_context() regardless of which thread ultimately executes them.
    """
    global _registered
    if _registered:
        logger.warning("audit service: register() called twice -- ignoring")
        return

    def _persist(event: AuditEvent) -> None:
        policy = get_policy(event.event_name)
        if policy.write_mode is WriteMode.SYNC:
            _write_now(event)
        else:
            _write_async(event, app)

    audit.register_listener(_persist)
    _registered = True
    logger.info("audit service: subscribed to shared.audit")


def _reset_for_tests() -> None:
    global _registered
    _registered = False
