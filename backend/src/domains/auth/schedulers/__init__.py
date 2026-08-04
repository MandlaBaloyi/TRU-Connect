"""
Auth's own child scheduler. Declares WHAT Auth wants scheduled and how
often -- see auth_scheduler.py. Owns no engine, no timer, no execution
machinery of its own; the Master Scheduler (src/master_scheduler/) runs
whatever this file declares.
"""
