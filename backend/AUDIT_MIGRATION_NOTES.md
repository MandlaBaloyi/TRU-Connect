# Audit domain reorganization -- migration notes

## Delete these old files (superseded by the new nested locations)

```
backend/src/domains/security/models/audit_event.py
backend/src/domains/security/repositories/audit_repository.py
backend/src/domains/security/services/audit_service.py
backend/src/domains/security/schemas/audit_schemas.py
backend/src/domains/security/rules/event_config.py
backend/src/domains/security/**/*.importfix.bak   (any remaining)
backend/src/shared/audit.py.bak
```

`security/rules/thresholds.py` is UNCHANGED and stays exactly where it
is -- it's a general Auth threshold (unverified-email expiry), not
audit-specific, even though it happens to sit in the security domain.

`security/detection/` is UNCHANGED and stays a sibling to the new
`security/audit/` package, not nested inside it.

## Update src/__init__.py

```python
# OLD:
from src.domains.security.services import audit_service
audit_service.register()

# NEW:
from src.domains.security.audit.services import audit_service
audit_service.register(app)
```

Note the signature change: `register()` now REQUIRES the real Flask
`app` instance -- this is part of the app-context bug fix below, not
just the path move. If you already have the Master Scheduler's `trigger`
import right below this, order doesn't matter between the two, but this
line must still come after `_register_extensions(app)` (same as before).

## THE APP-CONTEXT BUG -- FOUND AND FIXED, NOT JUST MOVED

**Original symptom:** every ASYNC-classified audit event (OTP created,
token created, most high-volume events) silently failed to persist,
logging `RuntimeError: Working outside of application context`.

**Root cause:** `_write_async()` handed a deferred callable to
`shared.queue.enqueue()`, which runs it on a DIFFERENT THREAD, after the
original request's Flask app context had already ended. `db.session`
needs an active app context to resolve, and by the time the background
thread picked up the job, that context was gone.

**The fix:** `register(app)` now captures the real Flask `app` instance
in a closure. Every deferred (ASYNC) write is wrapped in
`app.app_context()` at the exact point it executes, regardless of which
thread that turns out to be. This no longer depends on whether
`shared.queue`'s worker thread happens to preserve Flask's context.

**Verified against real Postgres with a genuine background thread**
(not a simulated/inline stub) -- see the new
`tests/domains/security/audit/test_audit_service.py`, specifically
`test_async_event_persists_when_executed_on_a_real_background_thread`,
which would have failed with the original bug's RuntimeError and now
passes. SYNC events and the double-registration guard were also
confirmed unaffected by the fix.

## Also check manually (not auto-fixed, file not available to this generator)

If `security/models/__init__.py` (the OLD, now largely empty, generic
folder) has a line like:
```python
from src.domains.security.models.audit_event import AuditEventRecord  # noqa: F401
```
(added per the original INTEGRATION_AUDIT.md, for Alembic autogenerate
discovery), update it to import from the NEW location instead:
```python
from src.domains.security.audit.models.audit_event import AuditEventRecord  # noqa: F401
```
or move this import into `security/audit/models/__init__.py` (already
created with this exact import) and ensure wherever your app registers
all models for Alembic imports that package.

## Verified before shipping

Full audit test suite (11 tests) run against this exact reorganized
structure and real Postgres, including the append-only trigger being
genuinely exercised (UPDATE and DELETE both confirmed rejected).
