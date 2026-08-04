"""Repository behaviour against real Postgres -- unchanged logic, import
paths moved to security.audit.models/repositories."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from src.domains.security.audit.models.audit_event import AuditEventRecord
from src.domains.security.audit.repositories.audit_repository import AuditRepository


def _event(**overrides):
    defaults = dict(
        id=uuid.uuid4(), timestamp=datetime.now(timezone.utc), domain="auth",
        event_name="auth.login_failed", status="failure", actor_type="user",
        email="a@example.com", event_metadata={},
    )
    defaults.update(overrides)
    return AuditEventRecord(**defaults)


def test_insert_roundtrip(db_session):
    rec = AuditRepository.insert(_event(email="round@example.com"))
    found = db_session.query(AuditEventRecord).filter_by(id=rec.id).first()
    assert found is not None
    assert found.email == "round@example.com"
