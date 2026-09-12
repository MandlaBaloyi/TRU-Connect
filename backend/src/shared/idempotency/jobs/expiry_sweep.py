"""
Job service: removes idempotency rows nobody will ever replay.

A stored response is worthless once the client has stopped retrying,
and these rows hold a hash of a request body plus whatever the
response contained -- so keeping them indefinitely would be a
retention problem invented for no benefit.

Pure job-service contract, same as every other job here: no arguments,
returns a JobResult, has no idea it is scheduled.
"""
from __future__ import annotations

import logging

from src.shared.idempotency import service as idempotency
from src.shared.scheduling.scheduling_types import JobResult

logger = logging.getLogger(__name__)


def run() -> JobResult:
    try:
        removed = idempotency.purge_expired()
    except Exception:  # noqa: BLE001
        logger.exception("idempotency: expiry sweep failed")
        return JobResult(success=False, count=0, detail="sweep failed")
    return JobResult(success=True, count=removed, detail=f"{removed} expired keys removed")
