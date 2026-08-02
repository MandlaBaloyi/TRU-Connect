# Security audit platform — integration steps

This generator creates new files and REPLACES `src/shared/audit.py`
(the original is backed up as `src/shared/audit.py.bak`).

## 1. Run the migration

```powershell
flask db upgrade
```

Creates `security.audit_events`, its indexes, and the append-only trigger.
If your Alembic head is not `acccb39c3c86`, edit `down_revision` at the top
of `migrations/versions/b1a2c3d4e5f6_security_audit_events.py` to match
`flask db current` before running.

## 2. Register the model for autogenerate

Make sure the new model is imported wherever your other models are
registered (so Alembic sees it), e.g. in `src/domains/security/models/__init__.py`:

```python
from src.domains.security.models.audit_event import AuditEventRecord  # noqa: F401
```

## 3. Subscribe the audit service at startup

In `src/__init__.py`, inside `create_app()`, next to the scheduler line
you already added:

```python
    from src.domains.security.services import audit_service
    audit_service.register()

    from src.domains.platform.schedulers import trigger
    trigger.start(app)

    return app
```

Order matters only in that `audit_service.register()` should come before
anything that might publish an event.

## 4. Nothing else changes

`auth_service.py`, `otp_service.py` and `password_reset_service.py` need
**zero edits**. Their existing `audit.log_*()` calls keep the same names
and signatures and now persist automatically.

## What still needs doing (not blocking)

- **New call sites.** `shared/audit.py` gained functions for OTP, tokens,
  logout and registration events that nothing calls yet. Wire them into
  the relevant services one at a time — each is additive and independent.
- **`ACCOUNT_*` / `ROLE_CHANGED` / `PERMISSION_CHANGED`** are defined in
  the enum but have no publisher, because no admin account-management
  feature exists yet. Expected.
- **No API routes.** `security/api/` stays empty until the control center
  exists. The repository and the RBAC field groups are the pieces that
  make that route thin when it comes.
- **Detection is interfaces only** (Phase 2 builds real detectors).
  Account lockout deliberately stays synchronous in the Auth domain.

## Verifying it works

Start the app, attempt a failed login, then:

```sql
SELECT event_name, status, email, ip_address, severity, correlation_id
FROM security.audit_events ORDER BY timestamp DESC LIMIT 5;
```
