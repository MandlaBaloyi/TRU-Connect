"""
Centralized tunable BUSINESS constants — not scheduling intervals. "How
often a job runs" is a Platform ("when") decision and lives in
src/domains/platform/schedulers/registry.py's JOB_SPECS list instead.

This file holds only thresholds that carry business MEANING: e.g. how old
an unverified email must be before it counts as "abandoned." These are
version-controlled, reviewable-in-a-diff values, not per-environment
config, so they live here in code rather than in .env.

To change how old an account must be before cleanup deletes it, change
UNVERIFIED_EMAIL_CLEANUP_DAYS below. To change how OFTEN that cleanup
runs, edit the interval in platform/schedulers/registry.py instead — two
different, deliberately separated decisions.
"""

# How old (in days) an unverified-EMAIL account must be before the cleanup
# job deletes it. Concerns User.verification_status only — see the scope
# note in auth/jobs/cleanup_unverified_emails.py for why this is not the
# same thing as future business/supplier profile verification.
UNVERIFIED_EMAIL_CLEANUP_DAYS: float = 7

# Rows deleted per batch, to avoid holding a long table lock on a single
# giant DELETE if the abandoned-row count ever grows large.
UNVERIFIED_EMAIL_CLEANUP_BATCH_SIZE: int = 500
