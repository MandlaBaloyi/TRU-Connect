"""
Products' own scheduled jobs. Same convention as
media/schedulers/media_scheduler.py: this file only DECLARES jobs --
the logic lives in jobs/, master_scheduler/registry.py decides how
they actually run.

Checked every 5 minutes -- deliberately short, independent of the
sweep's own grace period (7 real days, see deleted_product_media_sweep
.py's own docstring for the "FOR TESTING" 5-minute override). A short
check interval costs almost nothing (one cheap indexed query, empty
result the overwhelming majority of the time) and means testing with
the 5-minute override doesn't require an also-long wait for the next
scheduler tick on top of it.
"""
from __future__ import annotations

from src.domains.supplier.products.jobs import deleted_product_media_sweep
from src.master_scheduler.interfaces import JobSpec

JOB_SPECS: list[JobSpec] = [
    JobSpec(
        name="products_deleted_product_media_sweep",
        func=deleted_product_media_sweep.run,
        interval_seconds=300,
    ),
]
