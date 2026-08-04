"""Append-only enforcement -- the compliance property the audit design
rests on. Import paths moved to security.audit.models/repositories.
REQUIRES REAL POSTGRES (the guarantee is a database trigger)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import DatabaseError

from src.domains.security.audit.models.audit_event import AuditEventRecord
from src.domains.security.audit.repositories.audit_repository import AuditRepository
from src.extensions import db


@pytest.fixture(autouse=True)
def _ensure_append_only_trigger(app):
    """
    Re-applies the append-only trigger before every test in THIS FILE
    specifically. db.create_all()/drop_all() (in the shared `app`
    fixture) only knows about SQLAlchemy model metadata -- it has no
    idea the trigger exists, because it's pure migration DDL, never
    part of AuditEventRecord's model definition. The first test in a
    session gets lucky (the table still carries the trigger from
    `flask db upgrade`), but drop_all() in that test's teardown drops
    the table -- and with it, the trigger -- so the next test's
    create_all() rebuilds a bare table from the model alone, with no
    trigger at all. This re-applies the exact same DDL from
    migrations/versions/b1a2c3d4e5f6_security_audit_events.py,
    idempotently, before every test here, so these two tests are
    correct regardless of execution order.

    Scoped to THIS FILE alone (not a directory-level conftest.py) --
    test_audit_context.py's own `app` fixture is a bare Flask instance
    with no database at all, and this fixture broke it when it
    previously lived at the directory level.
    """
    if db.engine.dialect.name != "postgresql":
        yield
        return

    db.session.execute(db.text("""
        CREATE OR REPLACE FUNCTION security.reject_audit_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_events is append-only: % is not permitted', TG_OP
                USING HINT = 'Audit records are immutable for compliance. '
                             'To archive, disable this trigger explicitly.';
        END;
        $$ LANGUAGE plpgsql;
    """))
    db.session.execute(db.text(
        "DROP TRIGGER IF EXISTS trg_audit_events_append_only ON security.audit_events"
    ))
    db.session.execute(db.text("""
        CREATE TRIGGER trg_audit_events_append_only
        BEFORE UPDATE OR DELETE ON security.audit_events
        FOR EACH ROW EXECUTE FUNCTION security.reject_audit_mutation();
    """))
    db.session.commit()

    yield


def test_update_is_rejected(db_session):
    if db.engine.dialect.name != "postgresql":
        pytest.skip("requires postgres")
    record = AuditRepository.insert(AuditEventRecord(
        id=uuid.uuid4(), timestamp=datetime.now(timezone.utc), domain="auth",
        event_name="auth.login_failed", status="failure", actor_type="user", event_metadata={},
    ))
    with pytest.raises(DatabaseError):
        db.session.execute(
            db.text("UPDATE security.audit_events SET status = 'success' WHERE id = :i"),
            {"i": str(record.id)},
        )
        db.session.commit()
    db.session.rollback()


def test_delete_is_rejected(db_session):
    if db.engine.dialect.name != "postgresql":
        pytest.skip("requires postgres")
    record = AuditRepository.insert(AuditEventRecord(
        id=uuid.uuid4(), timestamp=datetime.now(timezone.utc), domain="auth",
        event_name="auth.login_failed", status="failure", actor_type="user", event_metadata={},
    ))
    with pytest.raises(DatabaseError):
        db.session.execute(
            db.text("DELETE FROM security.audit_events WHERE id = :i"),
            {"i": str(record.id)},
        )
        db.session.commit()
    db.session.rollback()