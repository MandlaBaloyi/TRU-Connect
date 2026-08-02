"""
Platform scheduling infrastructure. Owns EXECUTION only — when things run,
how they run safely, and what engine actually ticks the clock.

Owns no business logic (that lives in each domain's own jobs/ package) and
is not responsible for monitoring/health/history (that's Security's job,
via security/schedulers/monitor.py, which listens to this package's
runner but is never imported by it).

Files:
    interfaces.py  — the SchedulerEngine contract every concrete engine
                      must satisfy. Everything else in this codebase talks
                      to this contract, never to a concrete engine.
    engine.py       — the ONLY file allowed to import apscheduler. Swap
                      engines later by writing a new class here and
                      changing one line in trigger.py.
    registry.py     — the explicit list of what's scheduled and how often.
                      Imports job services FROM business domains INTO
                      platform (the dependency runs this direction only).
    runner.py       — wraps every job in uniform logging/timing/exception
                      isolation, and publishes JobExecutionOutcome events
                      for Security to listen to.
    trigger.py       — application startup hook. Starts the engine exactly
                      once, with a guard against Flask's debug-mode
                      reloader double-starting it.
"""
