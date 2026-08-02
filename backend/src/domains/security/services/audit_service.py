"""
Security's audit service — subscribes to shared.audit and persists events.

This is the ONLY place that turns a transport-level AuditEvent dataclass
into a database row. Auth has no idea this file exists; it publishes to
shared.audit, and this service registers itself as a listener at startup.
Dependency direction: Security -> shared <- Auth.

WRITE MODE is decided per-event by security/rules/event_config.py:
  SYNC  -> insert immediately, inside the caller's request
  ASYNC -> hand to shared/queue.py, written off the request thread

Persistence failures are logged and swallowed, never raised — see the
note in shared/audit.publish(). A login that succeeded must not become a
500 because the audit table was unreachable.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.domains.security.models.audit_event import AuditEventRecord
from src.domains.security.repositories.audit_repository import AuditRepository
from src.domains.security.rules.event_config import WriteMode, get_policy
from src.shared import audit
from src.shared.audit_types import AuditEvent

logger = logging.getLogger(__name__)

_registered = False


def to_record(event: AuditEvent) -> AuditEventRecord:
    """
    Map the transport dataclass onto the persistence model.

    Category and severity are filled from event_config here rather than by
    the publisher: classification is a Security-domain judgement, and
    baking it into Auth's call sites would mean re-deploying Auth to
    change how seriously Security treats an event.
    """
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


def persist(event: AuditEvent) -> None:
    """Listener entry point — called by shared.audit.publish()."""
    policy = get_policy(event.event_name)
    if policy.write_mode is WriteMode.SYNC:
        _write_now(event)
    else:
        _write_async(event)


def _write_now(event: AuditEvent) -> None:
    try:
        AuditRepository.insert(to_record(event))
    except Exception:  # noqa: BLE001 — auditing must never break the audited action
        logger.exception("failed to persist audit event=%s", event.event_name.value)


def _write_async(event: AuditEvent) -> None:
    """
    Route through the existing shared/queue.py abstraction rather than
    spawning a thread here. Today that queue runs an in-process background
    worker; when Redis/Celery is introduced, ASYNC becomes a real
    distributed queue with no change to this file, to event_config.py, or
    to any publisher.

    If the queue is unavailable for any reason, fall back to a synchronous
    write rather than dropping the event — a slightly slower request is a
    better outcome than a missing audit record.
    """
    try:
        from src.shared.queue import enqueue  # imported lazily: see fallback below

        enqueue(lambda: _write_now(event))
    except Exception:  # noqa: BLE001
        logger.warning(
            "audit queue unavailable for event=%s, falling back to synchronous write",
            event.event_name.value,
        )
        _write_now(event)


def register() -> None:
    """
    Subscribe to shared.audit. Called once at application startup (see
    INTEGRATION.md). Guarded against double-registration, which would
    otherwise write every event twice — a real hazard given create_app()
    is called more than once in tests.
    """
    global _registered
    if _registered:
        logger.warning("audit service: register() called twice — ignoring")
        return
    audit.register_listener(persist)
    _registered = True
    logger.info("audit service: subscribed to shared.audit")


def _reset_for_tests() -> None:
    """Not for production use."""
    global _registered
    _registered = False
