"""
Notification publishing -- mirrors shared/audit/audit.py's own
mechanism exactly (register_listener/publish/_listeners), reusing a
pattern already proven in this exact codebase rather than inventing a
new one.

This module knows nothing about databases, roles, or stock orders. It
builds nothing itself -- callers construct a complete NotificationEvent
and hand it to publish(). It just makes sure that event reaches
whichever domain has registered to persist it. domains/platform/
notifications subscribes to this; it never reaches toward that domain.

WHY publish() ENQUEUES RATHER THAN WRITING SYNCHRONOUSLY: a business
confirming an order shouldn't wait on a notification row being written
before their own request returns -- same "the action succeeding must
never depend on a side-effect succeeding" reasoning already applied to
audit logging. Routed through shared.queue.enqueue(), the SAME
background job infrastructure EmailService, AuditService, and
BulkImport already use. That module's own docstring says exactly what
this gets for free: swapping the in-process thread pool for a real
message broker (Celery/RQ/SQS) later means changing shared/queue/
queue.py's own internals ONLY -- nothing here, and nothing at any call
site of publish(), needs to change when that day comes.
"""
from __future__ import annotations

import logging
from typing import Callable

from src.shared.notifications.notification_types import NotificationEvent
from src.shared.queue.queue import enqueue

logger = logging.getLogger("tru_connect.notifications")

_listeners: list[Callable[[NotificationEvent], None]] = []


def register_listener(callback: Callable[[NotificationEvent], None]) -> None:
    """Subscribe to published notifications. Called once at startup by
    the persisting domain's own service. A registry, not a direct
    import, for the exact same reason shared/audit's own
    register_listener is a registry -- this module must have zero
    dependency on whichever domain ends up persisting these."""
    _listeners.append(callback)


def clear_listeners() -> None:
    """Test helper -- lets a test isolate itself from real persistence,
    same purpose as shared/audit's own clear_listeners."""
    _listeners.clear()


def publish_notification(event: NotificationEvent) -> None:
    """Hands the event to every registered listener, via the shared
    background queue -- never blocks the caller's own request.

    NEVER RAISES SYNCHRONOUSLY. A notification failing to send must
    never break the real action that triggered it -- an order
    genuinely being confirmed must not become a 500 because a
    notification row couldn't be written. Same tradeoff already
    accepted for audit logging, for the same reason."""

    def _deliver() -> None:
        for listener in _listeners:
            try:
                listener(event)
            except Exception:  # noqa: BLE001 -- see docstring: a failed notification must never break the triggering action
                logger.exception("notification listener failed for category=%s", event.category.value)

    enqueue(_deliver)
