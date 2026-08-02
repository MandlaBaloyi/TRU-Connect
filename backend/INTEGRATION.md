# Platform scheduler integration — manual steps

This generator only CREATES new files. It does not touch app.py,
src/__init__.py, or any existing file. Add the following yourself so the
diff is visible and reviewable.

## Where — src/__init__.py, inside create_app()

Add near the bottom of `create_app()`, AFTER `_register_extensions(app)`
(which calls `db.init_app(app)`) and after `_register_blueprints(app)` —
right before `return app`:

```python
    from src.domains.platform.schedulers import trigger
    trigger.start(app)

    return app
```

That's it — one import, one call. `trigger.start(app)` internally:
- imports `security.schedulers.monitor` so it subscribes to job outcomes
- builds the APScheduler engine
- registers every job listed in `platform/schedulers/registry.py`
- wraps each job so it runs inside `app.app_context()` automatically
  (needed because `db.session` is Flask-context-bound)
- starts ticking

## Dependency

Already in your requirements.txt from the earlier round:
```
APScheduler==3.11.3
tzlocal==5.4.4
tzdata==2026.3
```

## Notes

- `trigger.start()` is safe to call more than once (no-op with a logged
  warning) and correctly skips starting in Werkzeug's debug-reloader
  watcher process, so `debug=True` in dev will not double-schedule jobs.
- Multi-worker production (Gunicorn with >1 worker) is NOT solved by this
  guard — that's a different problem (multiple OS processes, not Werkzeug
  reloading one process into two). If you run multiple Gunicorn workers,
  only start the trigger in one of them (e.g. gated by worker index, or
  run the scheduler as a separate process/service) — otherwise every
  worker runs its own tick. The cleanup job is idempotent (harmless if
  this happens), but it is wasted work and log noise. Flagged, not solved,
  matching the "single-process is fine for now" decision already made for
  the in-memory monitor state in security/schedulers/monitor.py.
- To add a new scheduled job later: write a `run()` function in the owning
  domain's `jobs/` package (returns a `JobResult`), then add one line to
  `JOB_SPECS` in `src/domains/platform/schedulers/registry.py`. Nothing
  else changes.
