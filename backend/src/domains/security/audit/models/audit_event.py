"""
The single enterprise audit table. Relocated from security/models/ to
security/audit/models/ -- content unchanged, only its location moved to
match Business's nested-per-feature convention.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.extensions import db


class AuditEventRecord(db.Model):
    __tablename__ = "audit_events"
    __table_args__ = ({"schema": "security"},)

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    domain = db.Column(db.String(50), nullable=False)
    module = db.Column(db.String(100), nullable=True)
    event_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    severity = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), nullable=False)
    failure_reason = db.Column(db.String(255), nullable=True)
    actor_type = db.Column(db.String(30), nullable=False, default="user")
    user_id = db.Column(UUID(as_uuid=True), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=True)
    tenant_id = db.Column(UUID(as_uuid=True), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    browser = db.Column(db.String(50), nullable=True)
    operating_system = db.Column(db.String(50), nullable=True)
    platform = db.Column(db.String(30), nullable=True)
    device_id = db.Column(db.String(255), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)
    correlation_id = db.Column(db.String(64), nullable=True)
    request_id = db.Column(db.String(64), nullable=True)
    http_method = db.Column(db.String(10), nullable=True)
    endpoint = db.Column(db.String(255), nullable=True)
    http_status_code = db.Column(db.Integer, nullable=True)
    event_metadata = db.Column("metadata", JSONB, nullable=False, default=dict)
