"""
IdempotencyKey -- the stored result of a request, so a retry returns
the same answer instead of doing the same thing twice.

THE FAILURE THIS PREVENTS (V2_13 §3.1). A supplier's ERP posts a
product. The connection times out at fifteen seconds. The ERP has no
way to know whether we processed it, so -- correctly -- it retries. We
create a SECOND product. Nobody notices until their catalogue has
doubled.

  ─────────────────────────────────────────────────────────────────────
  THIS CANNOT BE ENGINEERED AWAY ON THE CLIENT. If a request times out
  the caller genuinely cannot tell whether the server processed it.
  Retrying is CORRECT behaviour. The fix is on our side.
  ─────────────────────────────────────────────────────────────────────

SCOPED TO (key, user_id), not to the key alone. Clients generate keys
themselves, and two suppliers independently choosing the same UUID
must not see each other's responses -- which is exactly the kind of
cross-tenant leak a global key space invites.

THE REQUEST FINGERPRINT IS WHY THIS IS NOT JUST A CACHE. Reusing one
key for a DIFFERENT request is a client bug, and returning the first
response would hide it -- the caller would believe their second,
different request succeeded. Storing a hash of the body lets that be
refused loudly instead.

PLAIN db.Model, like the history tables: a stored response has no
business being soft-deleted, and rows leave by expiry alone.
"""
from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.core.base_model import utcnow
from src.extensions import db


class IdempotencyKey(db.Model):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        # ONE ROW PER (key, caller). The unique constraint is not
        # bookkeeping -- it is the concurrency control. Two simultaneous
        # retries race to INSERT, exactly one wins, and the loser is
        # told the request is already in flight rather than being let
        # through to do the work a second time.
        db.UniqueConstraint("key", "user_id", name="uq_idempotency_key_user"),
        db.Index("ix_idempotency_keys_expires_at", "expires_at"),
        {"schema": "idempotency"},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    #: The client's own Idempotency-Key header. Opaque to us -- Stripe
    #: suggests a v4 UUID, and anything with enough entropy works.
    key = db.Column(db.String(255), nullable=False)

    #: WHOSE key this is. Nullable only because a future unauthenticated
    #: idempotent endpoint is conceivable; every caller today has one.
    user_id = db.Column(UUID(as_uuid=True), nullable=True)

    #: Method + path, recorded so a key reused against a DIFFERENT
    #: endpoint is visible in the row rather than inferred.
    endpoint = db.Column(db.String(255), nullable=False)

    #: SHA-256 of the request body. See the class docstring.
    request_hash = db.Column(db.String(64), nullable=False)

    #: NULL while the request is still running. A row with a null
    #: status is a CLAIM, not a result -- which is what makes the
    #: in-flight case distinguishable from a completed one.
    status_code = db.Column(db.Integer, nullable=True)
    response_body = db.Column(JSONB, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    #: Rows are worthless after the client has stopped retrying.
    #: Twenty-four hours is Stripe's window and there is no reason to
    #: differ; the sweep in jobs/ removes them.
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    @property
    def is_complete(self) -> bool:
        return self.status_code is not None
