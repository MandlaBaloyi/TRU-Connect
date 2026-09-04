"""
Notification -- the real, persisted table shared/notifications'
publish mechanism ultimately writes to. Genuinely generic on purpose:
no order_id, no supplier_profile_id, nothing stock-order-specific
anywhere in this schema. related_entity_type/related_entity_id are the
ONLY link back to whatever this notification is actually about, and
they're deliberately untyped strings -- this table has no foreign key
into checkout.stock_orders, connections, or anything else, because a
real foreign key would mean this domain needs to know that table
exists at all. The tradeoff (no referential integrity enforced at the
DB level for that link) is accepted deliberately, matching this
domain's whole reason for existing: it forwards messages to the right
destination and does its own job, nothing more.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from src.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = ({"schema": "platform"},)

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False, index=True)

    # STOCK_ORDER or INBOX -- see NotificationCategory's own docstring
    # for the full reasoning on why just these two, for now.
    category = db.Column(db.String(20), nullable=False, index=True)

    # Short, template-built strings -- see domains/network/orders' own
    # notification_templates.py for where the actual wording lives.
    # This table stores whatever it's given; it never constructs text
    # itself.
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.String(500), nullable=False)

    # The one, deliberately generic link back to whatever this
    # notification is actually about -- e.g. ("stock_order", the
    # order's own id) -- lets a tapped notification deep-link
    # correctly without this table ever needing a real FK into that
    # other domain's own schema.
    related_entity_type = db.Column(db.String(50), nullable=True)
    related_entity_id = db.Column(db.String(100), nullable=True)

    is_read = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text("false"))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
