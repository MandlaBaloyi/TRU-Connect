"""
Platform's notification service -- subscribes to shared.notifications
and persists events. Mirrors security/audit/services/audit_service.py's
own subscription shape, INCLUDING its real, already-fixed app-context
bug (see that file's own docstring for the full original incident).

register(app) REQUIRES the real Flask app instance, captured via
closure -- shared/notifications/notifications.py's own
publish_notification() already routes through shared.queue.enqueue(),
which runs on a background thread pool AFTER the original request has
finished. db.session is Flask-SQLAlchemy's scoped session and needs an
ACTIVE app context to know which app it belongs to; without wrapping
this listener's own DB write in app.app_context() explicitly, every
notification would silently fail to persist with the exact
"RuntimeError: Working outside of application context" audit_service.py
already hit once. Applying that already-known fix here from the start,
not rediscovering it the hard way a second time.
"""
from __future__ import annotations

import logging

from flask import Flask

from src.core.exceptions import NotFoundError
from src.domains.platform.notifications.models.notification import Notification
from src.domains.platform.notifications.repositories.notification_repository import NotificationRepository
from src.shared.notifications import notifications
from src.shared.notifications.notification_types import NotificationEvent

logger = logging.getLogger("tru_connect.notifications")


class NotificationNotFoundError(NotFoundError):
    """Raised for a genuinely nonexistent notification, or one that
    exists but belongs to a different user -- deliberately
    indistinguishable, same IDOR-safety reasoning as every other
    domain in this codebase."""

    code = "NOTIFICATION_NOT_FOUND"

_registered = False


def register(app: Flask) -> None:
    """Subscribe to shared.notifications. Called once at application
    startup, same integration shape as audit_service.py's own
    register(app)."""
    global _registered
    if _registered:
        logger.warning("notification service: register() called twice -- ignoring")
        return

    def _persist(event: NotificationEvent) -> None:
        with app.app_context():
            try:
                NotificationRepository.create(
                    recipient_user_id=event.recipient_user_id,
                    category=event.category.value,
                    title=event.title,
                    body=event.body,
                    related_entity_type=event.related_entity_type,
                    related_entity_id=event.related_entity_id,
                )
            except Exception:  # noqa: BLE001 -- a failed notification must never break the action that triggered it
                logger.exception("failed to persist notification for category=%s", event.category.value)

    notifications.register_listener(_persist)
    _registered = True
    logger.info("notification service: subscribed to shared.notifications")


def _reset_for_tests() -> None:
    global _registered
    _registered = False


# =============================================================================
# READ-SIDE -- what the actual API routes call. Genuinely simple pass-
# throughs to the repository; kept here rather than a separate file
# since this is a small, cohesive surface, not a large one like
# cart_service/checkout_service that earned their own split.
# =============================================================================


def list_notifications(user_id, category: str | None = None) -> list[Notification]:
    return NotificationRepository.list_for_user(user_id, category)


def get_unread_count(user_id) -> int:
    return NotificationRepository.get_unread_count(user_id)


def mark_as_read(user_id, notification_id) -> Notification:
    """IDOR-safe by construction -- get_by_id_for_user is scoped to
    the requesting user, so a user genuinely cannot mark someone
    else's notification as read, even with a valid id."""
    notification = NotificationRepository.get_by_id_for_user(notification_id, user_id)
    if not notification:
        raise NotificationNotFoundError("Notification not found.")
    return NotificationRepository.mark_read(notification)


def mark_all_as_read(user_id) -> int:
    return NotificationRepository.mark_all_read(user_id)
