"""
Claiming, completing and replaying idempotency keys.

THE THREE OUTCOMES a request with a key can meet:

  NO ROW           first time. Claim it, run the handler, store what
                   it returned.
  COMPLETED ROW    a retry. Return the stored status and body without
                   running anything.
  CLAIMED ROW      another copy of this request is running RIGHT NOW.
                   Refuse with 409 rather than doing the work twice --
                   two simultaneous retries are the exact case the
                   unique constraint exists to arbitrate.

WHAT HAPPENS WHEN THE HANDLER FAILS, which is the genuinely hard
decision in this module and where we DEPART FROM STRIPE.

Stripe stores the result of the first request "regardless of whether
it succeeds or fails", so a retry of a request that 500ed returns the
same 500. That is the safest possible answer to "did the write
happen?" and we do not copy it.

  We store 2xx and 4xx, and RELEASE THE CLAIM on 5xx.

Two reasons. First, a 5xx here almost always means the handler raised,
which rolls the SQLAlchemy transaction back -- so there is no
half-created product to protect against, and the thing the key exists
to prevent did not happen. Second, caching a transient infrastructure
failure for twenty-four hours converts a retryable problem into an
unretryable one: the client's only recovery would be to invent a new
key, which is precisely the behaviour that produces duplicates.

THE NARROW RISK WE ACCEPT, stated rather than hidden: a handler whose
database work COMMITS and which then fails while serialising its
response would release the claim, and a retry could duplicate. That
window is small, and the alternative trades it for a much more common
harm.

4xx IS STORED because it is a deterministic answer about the request
itself -- a validation failure will fail identically on retry, and
replaying it saves the round trip without hiding anything.
"""
from __future__ import annotations

import hashlib
from datetime import timedelta
from typing import Optional

from src.core.base_model import utcnow
from src.extensions import db
from src.shared.idempotency.models import IdempotencyKey

#: How long a stored response stays replayable. Stripe's window, and
#: long enough to cover any sane retry schedule.
RETENTION = timedelta(hours=24)


class IdempotencyConflict(Exception):
    """Same key, different request body -- a client bug worth shouting
    about rather than papering over."""


class IdempotencyInFlight(Exception):
    """Another copy of this exact request is still running."""


def fingerprint(raw_body: bytes) -> str:
    """SHA-256 of the exact bytes. Hashed rather than stored because we
    only ever need to COMPARE it -- the body itself may hold personal
    data, and keeping a copy of every request for a day would be a
    retention problem invented for no benefit."""
    return hashlib.sha256(raw_body or b"").hexdigest()


def claim(key: str, user_id, endpoint: str, request_hash: str) -> Optional[IdempotencyKey]:
    """Reserve this key, or raise if it is already spoken for.

    Returns the new claim row on success. Raises IdempotencyInFlight if
    another request holds an incomplete claim, and IdempotencyConflict
    if the key was used for a different body.

    COMMITS THE CLAIM IMMEDIATELY, and it has to: the claim must be
    visible to the OTHER request racing us, and a row still sitting in
    our uncommitted transaction is visible to nobody. This is the one
    place in this module that owns a commit.
    """
    existing = _find(key, user_id)
    if existing is not None:
        if existing.request_hash != request_hash:
            raise IdempotencyConflict(
                "This Idempotency-Key was already used for a different request."
            )
        if not existing.is_complete:
            raise IdempotencyInFlight("A request with this Idempotency-Key is still in progress.")
        return existing

    row = IdempotencyKey(
        key=key,
        user_id=user_id,
        endpoint=endpoint,
        request_hash=request_hash,
        expires_at=utcnow() + RETENTION,
    )
    db.session.add(row)
    try:
        db.session.commit()
    except Exception:  # noqa: BLE001 -- almost certainly the unique index
        db.session.rollback()
        # LOST THE RACE. Another request inserted the same key between
        # our lookup and our insert, which is exactly what the
        # constraint is for. Re-read to tell "in flight" from
        # "finished while we were inserting".
        existing = _find(key, user_id)
        if existing is None:
            raise
        if existing.request_hash != request_hash:
            raise IdempotencyConflict(
                "This Idempotency-Key was already used for a different request."
            )
        if not existing.is_complete:
            raise IdempotencyInFlight("A request with this Idempotency-Key is still in progress.")
        return existing
    return row


def complete(row: IdempotencyKey, status_code: int, body) -> None:
    """Store the outcome so a retry replays it."""
    row.status_code = status_code
    row.response_body = body
    db.session.commit()


def release(row: IdempotencyKey) -> None:
    """Drop the claim so the client may genuinely retry.

    Called on 5xx and on an unhandled exception -- see the module
    docstring for why that is the right answer here and not Stripe's.
    """
    try:
        db.session.rollback()
        fresh = db.session.get(IdempotencyKey, row.id)
        if fresh is not None and not fresh.is_complete:
            db.session.delete(fresh)
            db.session.commit()
    except Exception:  # noqa: BLE001
        db.session.rollback()


def _find(key: str, user_id) -> Optional[IdempotencyKey]:
    return IdempotencyKey.query.filter_by(key=key, user_id=user_id).first()


def purge_expired(now=None) -> int:
    """Delete rows past their window. Returns how many went."""
    now = now or utcnow()
    deleted = IdempotencyKey.query.filter(IdempotencyKey.expires_at < now).delete(
        synchronize_session=False
    )
    db.session.commit()
    return deleted
