"""
Regression test for the app-context bug: ASYNC-classified audit events
were silently failing to persist because shared.queue.enqueue() runs its
callable on a different thread, after the original request's Flask app
context has already ended -- db.session needs an active app context to
resolve, and by the time the background thread picked up the job, that
context was long gone.

Deliberately uses a REAL background thread (not an inline stub), to
faithfully reproduce the original failure mode rather than accidentally
passing because a simplified test happens to stay on one thread.
"""

from __future__ import annotations

import threading

import pytest

from src.domains.security.audit.services import audit_service
from src.shared.audit import audit
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditStatus
from src.shared.audit.event_types.auth import AuthAuditEvent


@pytest.fixture(autouse=True)
def _reset(app):
    audit_service._reset_for_tests()
    audit.clear_listeners()
    yield
    audit_service._reset_for_tests()
    audit.clear_listeners()


def test_async_event_persists_when_executed_on_a_real_background_thread(app, db_session):
    """
    UNVERIFIED_ACCOUNT_EXPIRED is ASYNC per event_config.py. Publishing it
    triggers _write_async(), which hands a deferred callable to
    shared.queue.enqueue() -- exercised here via a REAL threading.Thread,
    not an inline call, so this test would have failed with the original
    bug's RuntimeError before the fix, and passes now because
    _write_async() wraps the deferred write in app.app_context() itself.
    """
    with app.app_context():
        audit_service.register(app)

        captured_exceptions = []

        def _publish_on_a_real_thread():
            try:
                with app.app_context():
                    audit.publish(
                        AuditEvent(
                            event_name=AuthAuditEvent.UNVERIFIED_ACCOUNT_EXPIRED,
                            domain=AuditDomain.AUTH,
                            status=AuditStatus.SUCCESS,
                            email="thread-test@example.com",
                        )
                    )
            except Exception as exc:  # pragma: no cover - only hit if the bug regresses
                captured_exceptions.append(exc)

        thread = threading.Thread(target=_publish_on_a_real_thread)
        thread.start()
        thread.join(timeout=5)

        assert not captured_exceptions, f"Publishing raised on a background thread: {captured_exceptions}"

        from src.domains.security.audit.models.audit_event import AuditEventRecord

        row = (
            db_session.query(AuditEventRecord)
            .filter_by(event_name=AuthAuditEvent.UNVERIFIED_ACCOUNT_EXPIRED.value)
            .first()
        )
        assert row is not None, "ASYNC event did not persist -- the app-context bug has regressed"
        assert row.email == "thread-test@example.com"


def test_sync_event_persists_immediately_unaffected_by_the_fix(app, db_session):
    """LOGIN_SUCCESS is SYNC -- confirms the fix didn't change SYNC behaviour."""
    import uuid

    with app.app_context():
        audit_service.register(app)
        audit.publish(
            AuditEvent(
                event_name=AuthAuditEvent.LOGIN_SUCCESS,
                domain=AuditDomain.AUTH,
                status=AuditStatus.SUCCESS,
                user_id=str(uuid.uuid4()),
            )
        )
        from src.domains.security.audit.models.audit_event import AuditEventRecord

        assert db_session.query(AuditEventRecord).filter_by(
            event_name=AuthAuditEvent.LOGIN_SUCCESS.value
        ).count() == 1


def test_register_called_twice_does_not_double_subscribe(app):
    with app.app_context():
        audit_service.register(app)
        audit_service.register(app)  # must not raise, must not double-subscribe
        assert len(audit._listeners) == 1
