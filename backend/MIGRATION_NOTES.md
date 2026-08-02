# Migration notes — v1 scheduler -> v2 platform architecture

If you already ran the EARLIER `generate_scheduler.py` against this repo
(the one that put a job registry directly under
`src/domains/security/schedulers/`), delete these — they are fully
superseded by this v2 generator:

```
src/domains/security/schedulers/registry.py
src/domains/security/schedulers/trigger.py
src/domains/security/schedulers/job_status.py
src/domains/auth/jobs/cleanup_unverified_accounts.py
tests/domains/security/schedulers/test_registry.py   (the OLD one, testing polling logic)
tests/domains/auth/jobs/test_cleanup_unverified_accounts.py
```

And remove the two lines from `src/__init__.py` if you already added them:
```python
import src.domains.auth.jobs.cleanup_unverified_accounts
from src.domains.security.schedulers import trigger
trigger.start()
```
Replace with the v2 lines from INTEGRATION.md (note: `trigger` now lives
under `platform`, not `security`, and `trigger.start()` now takes `app`).

## What changed and why

| v1 | v2 | Why |
|---|---|---|
| Registry lived in `security/schedulers/` | Lives in `platform/schedulers/` | Security should monitor, not execute — scheduling is an execution concern, owned by Platform. |
| Auth job self-registered on import (`auth -> security` dependency) | Auth job is a plain `run()` function; Platform imports it (`platform -> auth`) | Business domains must not depend on infrastructure. The dependency now points the correct direction. |
| Manual poll loop (`is_due` / `run_due_jobs` on a shared tick) | Each job scheduled directly via APScheduler's own per-job interval trigger | Simpler, and lets each job have its own real interval instead of everything sharing one poll granularity. |
| `cleanup_unverified_accounts` | `cleanup_unverified_emails` | Precision: this job only concerns email/OTP verification (`User.verification_status`). Once Business/Supplier profile verification (KYC-style) exists, "account" would be ambiguous between the two. |
| `JobResult` defined inside the registry module | `JobResult` / `JobExecutionOutcome` moved to `src/shared/scheduling_types.py` | Shared contract types belong in neutral ground, not owned by either side of the Platform<->Auth boundary. |
| No engine abstraction — registry called APScheduler indirectly | `interfaces.py` (`SchedulerEngine`) + `engine.py` (the only apscheduler import) | Swapping APScheduler for Celery/RQ/cron later touches only `engine.py`. |
| No monitoring/observer layer | `runner.py` publishes `JobExecutionOutcome` to listeners; `security/schedulers/monitor.py` subscribes | Security gets execution visibility (health, history, failure tracking) without owning the engine, matching "Auth publishes events, Security persists them" already established for the audit log. |
