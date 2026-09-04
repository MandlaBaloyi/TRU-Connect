"""
NotificationRepository -- pure CRUD, no business rules. Matches the
same "repository never decides, only persists" discipline as every
other repository in this codebase.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from src.domains.platform.notifications.models.notification import Notification
from src.extensions import db


class NotificationRepository:
    @staticmethod
    def create(
        recipient_user_id: str | uuid.UUID,
        category: str,
        title: str,
        body: str,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
    ) -> Notification:
        notification = Notification(
            id=uuid.uuid4(),
            recipient_user_id=recipient_user_id,
            category=category,
            title=title,
            body=body,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def list_for_user(user_id: str | uuid.UUID, category: Optional[str] = None) -> List[Notification]:
        query = Notification.query.filter_by(recipient_user_id=user_id)
        if category:
            query = query.filter_by(category=category)
        return query.order_by(Notification.created_at.desc()).all()

    @staticmethod
    def get_unread_count(user_id: str | uuid.UUID) -> int:
        return Notification.query.filter_by(recipient_user_id=user_id, is_read=False).count()

    @staticmethod
    def get_by_id_for_user(notification_id: str | uuid.UUID, user_id: str | uuid.UUID) -> Optional[Notification]:
        """IDOR-safe by construction, same discipline as everywhere
        else in this codebase -- a user genuinely cannot mark someone
        else's notification as read, even with a valid id."""
        return Notification.query.filter_by(id=notification_id, recipient_user_id=user_id).first()

    @staticmethod
    def mark_read(notification: Notification) -> Notification:
        notification.is_read = True
        db.session.commit()
        return notification

    @staticmethod
    def mark_all_read(user_id: str | uuid.UUID) -> int:
        """A real batch update, not a loop of individual mark_read
        calls -- same reasoning as clear_cart's own delete_all_items."""
        count = Notification.query.filter_by(recipient_user_id=user_id, is_read=False).update({"is_read": True})
        db.session.commit()
        return count
