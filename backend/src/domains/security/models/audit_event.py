"""
The single enterprise audit table.

ONE TABLE, NOT ONE PER DOMAIN. There is deliberately no auth_audit,
supplier_audit, wallet_audit. Every row self-identifies via domain /
module / event_name, which is what lets a future domain start publishing
without a schema change, and what lets the admin panel run one query
across the whole platform instead of UNIONing N tables.

APPEND-ONLY. Rows are inserted and never updated or deleted. This is
enforced at the database level by a trigger (see the migration), not just
by convention — historical integrity is a regulatory property, and a
convention is only as strong as the next person who writes a service.

DELIBERATELY NOT INHERITING BaseModel. BaseModel provides updated_at,
is_deleted and deleted_at, which are soft-delete/mutation affordances
that directly contradict append-only semantics. An audit row has no
"updated" state and must not be soft-deletable. It carries its own UUID
primary key and its own timestamp instead.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.extensions import db


class AuditEventRecord(db.Model):
    """Persisted form of src.shared.audit_types.AuditEvent."""

    __tablename__ = "audit_events"
    __table_args__ = (
        # Composite indexes chosen for the queries the admin control center
        # will actually run. This table only grows, so unindexed filters
        # degrade permanently rather than temporarily.
        db.Index("ix_audit_events_timestamp_desc", db.text("timestamp DESC")),
        db.Index("ix_audit_events_email_timestamp", "email", db.text("timestamp DESC")),
        db.Index("ix_audit_events_user_timestamp", "user_id", db.text("timestamp DESC")),
        db.Index("ix_audit_events_ip_timestamp", "ip_address", db.text("timestamp DESC")),
        db.Index("ix_audit_events_domain_event_timestamp", "domain", "event_name", db.text("timestamp DESC")),
        db.Index("ix_audit_events_correlation", "correlation_id"),
        db.Index("ix_audit_events_tenant_timestamp", "tenant_id", db.text("timestamp DESC")),
        {"schema": "security"},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- What / where from (classification) ---
    timestamp = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc), index=True,
    )
    domain = db.Column(db.String(50), nullable=False)
    module = db.Column(db.String(100), nullable=True)
    event_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    severity = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), nullable=False)
    failure_reason = db.Column(db.String(255), nullable=True)

    # --- Who ---
    actor_type = db.Column(db.String(30), nullable=False, default="user")
    # Intentionally NOT a ForeignKey to auth.users: an audit row must
    # survive deletion of the user it refers to (the cleanup job deletes
    # abandoned accounts, and an ON DELETE CASCADE would destroy exactly
    # the evidence of what happened to them). Referential integrity is
    # deliberately traded away for historical integrity.
    user_id = db.Column(UUID(as_uuid=True), nullable=True)
    # FULL email, never masked — masking is a presentation concern.
    email = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=True)
    tenant_id = db.Column(UUID(as_uuid=True), nullable=True)

    # --- Where from (network / device) ---
    ip_address = db.Column(db.String(45), nullable=True)  # 45 = max IPv6 length
    user_agent = db.Column(db.Text, nullable=True)
    browser = db.Column(db.String(50), nullable=True)
    operating_system = db.Column(db.String(50), nullable=True)
    platform = db.Column(db.String(30), nullable=True)
    device_id = db.Column(db.String(255), nullable=True)

    # --- Request correlation ---
    session_id = db.Column(db.String(255), nullable=True)
    correlation_id = db.Column(db.String(64), nullable=True)
    request_id = db.Column(db.String(64), nullable=True)
    http_method = db.Column(db.String(10), nullable=True)
    endpoint = db.Column(db.String(255), nullable=True)
    http_status_code = db.Column(db.Integer, nullable=True)

    # --- Extensibility: future domains attach domain-specific detail here
    #     without a migration. JSONB (not JSON) so it stays queryable. ---
    event_metadata = db.Column("metadata", JSONB, nullable=False, default=dict)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<AuditEvent {self.event_name} {self.status} at {self.timestamp}>"
