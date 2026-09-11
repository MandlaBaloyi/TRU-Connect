"""
domains/platform/notifications HTTP routes -- genuinely role-agnostic.

AUTH: @fully_authenticated only, deliberately NO @role_required
anywhere on this file -- unlike orders_routes.py's own business-only
scoping, a notification belongs to whichever user it was sent to,
regardless of whether that's a business, a supplier, or a future
admin. The recipient scoping itself comes from get_jwt_identity()
matching the notification's own recipient_user_id (see
NotificationRepository.get_by_id_for_user's own IDOR-safety
docstring), not from a role check.
"""
from __future__ import annotations

import uuid

from flask import Blueprint, request

from src.core.decorators import fully_authenticated, participants_only
from src.core.responses import success_response
from src.domains.platform.notifications.services import notification_service

notifications_bp = Blueprint("notifications", __name__)


def _user_id() -> uuid.UUID:
    from flask_jwt_extended import get_jwt_identity

    return uuid.UUID(get_jwt_identity())


def _serialize(notification) -> dict:
    return {
        "id": str(notification.id),
        "category": notification.category,
        "title": notification.title,
        "body": notification.body,
        "relatedEntityType": notification.related_entity_type,
        "relatedEntityId": notification.related_entity_id,
        "isRead": notification.is_read,
        "createdAt": notification.created_at.isoformat() if notification.created_at else None,
    }


@notifications_bp.route("/api/v1/notifications", methods=["GET"])
@fully_authenticated
@participants_only
def list_notifications():
    """?category=STOCK_ORDER or ?category=INBOX -- omit for both,
    matching the two real tabs this is built for."""
    category = request.args.get("category")
    results = notification_service.list_notifications(_user_id(), category)
    return success_response(data={"notifications": [_serialize(n) for n in results]})


@notifications_bp.route("/api/v1/notifications/unread-count", methods=["GET"])
@fully_authenticated
@participants_only
def get_unread_count():
    count = notification_service.get_unread_count(_user_id())
    return success_response(data={"count": count})


@notifications_bp.route("/api/v1/notifications/<uuid:notification_id>/read", methods=["POST"])
@fully_authenticated
@participants_only
def mark_as_read(notification_id: uuid.UUID):
    notification = notification_service.mark_as_read(_user_id(), notification_id)
    return success_response(data=_serialize(notification))


@notifications_bp.route("/api/v1/notifications/read-all", methods=["POST"])
@fully_authenticated
@participants_only
def mark_all_as_read():
    count = notification_service.mark_all_as_read(_user_id())
    return success_response(data={"markedRead": count})
