"""
Job service: hard-deletes NetworkInvitations that were never used
(still PENDING) and have passed their own expiry.

SCOPE -- PENDING ONLY, not REGISTERED. A REGISTERED invitation (someone
already used the ticket to register, just hasn't verified yet) is left
alone here -- that person's ACCOUNT is what actually needs to go, and
that's already auth/jobs/cleanup_unverified_emails.py's job, on its own
schedule. This job cleaning up a REGISTERED row while the account still
exists would orphan a real registration in progress. Once that OTHER
job does delete the account, this table's own invited_user_id already
goes to NULL automatically (ON DELETE SET NULL, see migration
2ea418343d1b_network_invitation_fk_set_null.py) -- so a REGISTERED
invitation whose linked account is gone becomes invited_user_id=NULL,
status=REGISTERED forever, a harmless orphaned row, not a blocker.
Sweeping THOSE up too is a reasonable future addition to this same job,
not required for correctness today.

Same pure-job-service contract as every other job in this codebase
(order_book/jobs/auto_clear_sweep_job.py, auth/jobs/
cleanup_unverified_emails.py): takes no arguments, returns a
JobResult, has no idea it's scheduled. Only this domain's own
scheduler file (schedulers/connections_scheduler.py) knows this
function is on a timer.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.domains.network.connections.models.network_invitation import InvitationStatus, NetworkInvitation
from src.extensions import db
from src.shared.scheduling.scheduling_types import JobResult

logger = logging.getLogger(__name__)


def run() -> JobResult:
    """
    Deletes every NetworkInvitation still PENDING (never used) whose
    expires_at has passed. Bulk delete, same hard-delete reasoning as
    auth's own cleanup job for abandoned records -- an expired,
    never-used ticket has no ongoing state anywhere else that would
    make a soft-delete meaningful.

    Must run inside an active Flask app context (db.session is
    context-bound) -- Master Scheduler's trigger guarantees this
    automatically, same as every other registered job.
    """
    now = datetime.now(timezone.utc)

    deleted_count = (
        NetworkInvitation.query.filter(
            NetworkInvitation.status == InvitationStatus.PENDING,
            NetworkInvitation.expires_at < now,
        ).delete(synchronize_session=False)
    )
    db.session.commit()

    detail = f"deleted {deleted_count} expired, never-used invitation(s)"
    logger.info("connections_expired_invitations_cleanup: %s", detail)
    return JobResult(success=True, count=deleted_count, detail=detail)
