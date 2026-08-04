# Master Scheduler reorganization -- migration notes

## Delete these old files (superseded by the new locations)

```
backend/src/domains/platform/schedulers/engine.py
backend/src/domains/platform/schedulers/interfaces.py
backend/src/domains/platform/schedulers/registry.py
backend/src/domains/platform/schedulers/runner.py
backend/src/domains/platform/schedulers/trigger.py
backend/src/domains/platform/schedulers/*.importfix.bak   (any remaining)
```

The folder itself stays -- it now holds ONLY Platform's own child
scheduler (`platform_scheduler.py`), the same shape as Auth's
`domains/auth/schedulers/auth_scheduler.py`.

## Update src/__init__.py

```python
# OLD:
from src.domains.platform.schedulers import trigger
trigger.start(app)

# NEW:
from src.master_scheduler import trigger
trigger.start(app)
```

The `audit_service.register(app)` line above it is unaffected by THIS
reorg -- see AUDIT_MIGRATION_NOTES.md for that one.

## Why the Master moved out of domains/platform/

Platform is one of five coordinated domains (Auth / Business / Supplier /
Wallet / Platform), not the coordinator itself -- so the coordinator
can't live inside one of the things it coordinates. It now sits at
`src/master_scheduler/`, a sibling to `src/core/` and `src/shared/`.

## What changed structurally

- `registry.py` no longer defines any job itself -- it imports each
  domain's own `JOB_SPECS` and concatenates them into `ALL_JOB_SPECS`.
  A dedicated test (`test_registry_defines_no_jobs_itself`) inspects the
  actual source to confirm this structurally, not just behaviourally.
- Adding a job to an EXISTING domain means editing only that domain's own
  scheduler file -- registry.py needs no change.
- Adding the FIRST job for a brand-new domain means one import + one line
  in registry.py's ALL_JOB_SPECS.

## Verified before shipping

Full scheduler test suite (12 tests) run against this exact structure,
including starting a real APScheduler engine and confirming the Master
correctly collects cleanup_unverified_emails from Auth's own scheduler
file while Platform's list is (correctly) empty.
