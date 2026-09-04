"""
Notification event contract -- neutral ground, mirroring shared/audit's
own audit_types.py exactly (same reasoning applies word for word: living
in shared/ is what keeps the dependency arrow correct -- any publisher
(orders today; connections, a future admin broadcast, later) imports
this; the persisting domain (domains/platform/notifications) imports
this too; neither imports the other).

Deliberately NOT stock-order-shaped. NotificationEvent knows nothing
about orders, prices, or suppliers -- title and body are already-built
strings by the time they arrive here (the CALLER constructs its own
wording -- see domains/network/orders' own notification_templates.py
for where that actually happens). This is exactly what makes the
"notifications domain doesn't need to know what a stock order is"
requirement real rather than aspirational: it structurally CANNOT know,
since nothing about that concept is represented in this type at all.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


class NotificationCategory(str, enum.Enum):
    """The two tabs, exactly as specified -- STOCK_ORDER for real order
    transaction messages, INBOX for everything else (system/platform
    messages). Deliberately just two for now, same "model only as far
    ahead as genuinely known" discipline as ConnectionRequestStatus and
    StockOrderStatus before it -- a third category gets added the day a
    real feature needs one, not speculatively now."""

    STOCK_ORDER = "STOCK_ORDER"
    INBOX = "INBOX"


@dataclass
class NotificationEvent:
    """One notification, ready to persist. recipient_user_id is
    deliberately just a user id -- no role field anywhere on this type,
    since a User already carries its own role and this event has no
    business caring which one; the exact same shape works whether the
    recipient is a business, a supplier, or a future admin.

    related_entity_type/related_entity_id are optional and generic
    (e.g. "stock_order", the order's own id) -- what lets a tapped
    notification deep-link back to the real thing it's about, without
    this type ever needing to know the specific shape of every entity
    that might someday send a notification through it."""

    recipient_user_id: str | UUID
    category: NotificationCategory
    title: str
    body: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
