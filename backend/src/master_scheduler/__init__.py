"""
Master Scheduler.

The Master Scheduler coordinates. It does not run business jobs itself
-- it owns the one shared execution engine, the one safe-execution
wrapper, and the one startup trigger, and it asks every domain "what do
you want scheduled?" rather than knowing that answer itself.

    Master Scheduler
            |
     +------+-------+--------+
     |      |       |        |
     v      v       v        v
    Auth  Business Supplier Platform
  Scheduler Scheduler Scheduler Scheduler
   (each domain's OWN file, e.g.
    domains/auth/schedulers/auth_scheduler.py,
    listing that domain's own jobs)

WHY THIS LIVES OUTSIDE domains/, as a sibling to core/ and shared/,
rather than nested inside domains/platform/ (where it used to live):
Platform is just one of the coordinated domains, not the coordinator --
the same category error as a CEO's office sitting inside one regional
branch. A cross-cutting coordinator belongs at the same level as the
other cross-cutting concerns (core/, shared/), not inside any one of the
things it coordinates.

Files:
    interfaces.py -- SchedulerEngine contract + the JobSpec shape every
                     domain's own scheduler file constructs. The ONLY
                     file every domain-owned scheduler file needs to
                     import from here -- importing this never creates a
                     circular dependency with registry.py, since
                     interfaces.py imports nothing domain-specific.
    engine.py      -- the ONLY file allowed to import apscheduler.
    runner.py      -- safe-execution wrapper + the observer hook Security
                      listens through (security/schedulers/monitor.py).
    registry.py    -- collects every domain's JOB_SPECS and hands them to
                      the engine. Defines NO jobs itself.
    trigger.py     -- application startup hook.
"""
