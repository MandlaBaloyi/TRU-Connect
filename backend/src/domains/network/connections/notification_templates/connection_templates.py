"""
connection_templates.py -- the real wording for connection-related
notifications. Mirrors domains/network/orders' own
notification_templates/stock_order_templates.py exactly in shape and
reasoning -- see that file's own module docstring for the full "why a
dedicated folder per domain" explanation.

CATEGORY IS DELIBERATELY INBOX, NOT STOCK_ORDER -- confirmed directly
during planning: a connection request is a relationship event, not a
transaction, and mixing the two tabs would defeat the entire reason
they were split in the first place.

ONLY TWO TEMPLATES EXIST HERE, DELIBERATELY -- a real decline
notification was explicitly NOT built, confirmed directly: unlike a
declined stock order (where there's a clear next step -- try a
different payment method), a declined connection is more personal, and
whether it deserves an unprompted notification at all was a genuine,
unresolved judgment call, not an oversight. Same reasoning applies to
ENDED (disconnect) -- not addressed yet either, left for a future,
explicit decision rather than assumed.
"""
from __future__ import annotations

from src.shared.notifications.notification_types import NotificationCategory, NotificationEvent


def build_connection_request_notification(
    recipient_user_id: str, requester_name: str, related_entity_id: str
) -> NotificationEvent:
    """To whoever RECEIVES a new connection request -- either
    direction (a business requesting a supplier, or a supplier
    requesting a business), since recipient_user_id is genuinely just
    a user id with no role baked into this function at all."""
    return NotificationEvent(
        recipient_user_id=recipient_user_id,
        category=NotificationCategory.INBOX,
        title="New connection request",
        body=f"TruConnect: {requester_name} wants to connect with you",
        related_entity_type="connection_request",
        related_entity_id=related_entity_id,
    )


def build_connection_accepted_notification(
    recipient_user_id: str, accepter_name: str, related_entity_id: str
) -> NotificationEvent:
    """To whoever ORIGINALLY SENT the request, once the other side
    accepts it."""
    return NotificationEvent(
        recipient_user_id=recipient_user_id,
        category=NotificationCategory.INBOX,
        title="Connection accepted",
        body=f"TruConnect: {accepter_name} accepted your connection request",
        related_entity_type="connection_request",
        related_entity_id=related_entity_id,
    )
