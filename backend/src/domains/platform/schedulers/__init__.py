"""
Platform's own child scheduler -- declares WHAT Platform wants scheduled,
per the Master Scheduler architecture. This folder used to also house
the Master's own engine/registry/runner/trigger; those moved to
src/master_scheduler/ (a sibling to core/ and shared/), since Platform is
just one of the coordinated domains, not the coordinator itself -- the
same reasoning that gives Auth its own domains/auth/schedulers/ file
rather than the Master's machinery living inside Auth.
"""
