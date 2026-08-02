"""
Append-only enforcement — the compliance property the whole audit design
rests on.

REQUIRES REAL POSTGRES: the guarantee is a database trigger, so it cannot
be verified on SQLite. Skipped automatically elsewhere, because a test
that silently passes without exercising the trigger would be worse than
no test at all.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import DatabaseError

from src.domains.security.models.audit_event import AuditEventRecord
from src.domains.security.repositories.audit_repository import AuditRepository
from src.extensions import db


def _is_postgres() -> bool:
    return db.session.bind.dialect.name == "postgresql"


pytestmark = pytest.mark.skipif(
    "not config.getoption('--run-pg', default=False)",
    reason="append-only trigger requires real Postgres",
)


def test_update_is_rejected(db_session):
    if not _is_postgres():
        pytest.skip("requires postgres")
    record = AuditRepository.insert(AuditEventRecord(
        id=uuid.uuid4(), timestamp=datetime.now(timezone.utc),
        domain="auth", event_name="auth.login_failed", status="failure",
        actor_type="user", event_metadata={},
    ))
    with pytest.raises(DatabaseError):
        db.session.execute(
            db.text("UPDATE security.audit_events SET status = 'success' WHERE id = :i"),
            {"i": str(record.id)},
        )
        db.session.commit()


def test_delete_is_rejected(db_session):
    if not _is_postgres():
        pytest.skip("requires postgres")
    record = AuditRepository.insert(AuditEventRecord(
        id=uuid.uuid4(), timestamp=datetime.now(timezone.utc),
        domain="auth", event_name="auth.login_failed", status="failure",
        actor_type="user", event_metadata={},
    ))
    with pytest.raises(DatabaseError):
        db.session.execute(
            db.text("DELETE FROM security.audit_events WHERE id = :i"),
            {"i": str(record.id)},
        )
        db.session.commit()
