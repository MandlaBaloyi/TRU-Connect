"""
Bulk Import's own feature-level config -- separate from rate_limit/
policies.py (that's specifically about per-request throttling; this is
about the feature being on at all).

BULK_IMPORT_ENABLED is the real "worse scenario" safety valve: if
bulk import were ever genuinely being abused at a scale beyond what
per-account lockout (see services/abuse_tracking.py) and the thread-
pool's own concurrency ceiling (shared/queue/queue.py) can absorb, this
is the manual, no-deploy-needed way to turn the whole feature off
platform-wide while the real cause gets investigated. Checked once, at
the very top of the submit route -- nothing downstream needs to know
this exists.
"""
from __future__ import annotations

import os


def is_bulk_import_enabled() -> bool:
    return os.environ.get("BULK_IMPORT_ENABLED", "true").lower() != "false"
