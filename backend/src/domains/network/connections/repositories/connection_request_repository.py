"""
ConnectionRequest repository -- ONLY talks to SQLAlchemy, no business
rules (same rule as every other repository in this codebase).

get_for_business_and_supplier / get_by_id_and_supplier_profile /
get_by_id_and_business are the ownership-scoped fetches every service
method should go through -- see loan_book_service.py's own docstring
on why baking ownership into the fetch itself (rather than fetching
by id then checking afterward) is the actual authorization mechanism,
not a courtesy.

GENERALIZED for both initiation directions -- see connection_request.py's
own docstring on initiated_by_role. list_pending_for_supplier_profile
now only returns BUSINESS-initiated rows (the supplier owes the
approval); the new list_pending_for_business is the mirror, only
SUPPLIER-initiated rows (the business owes the approval). Without this
split, each side's "requests I need to act on" list would incorrectly
include requests it created itself and is waiting on the OTHER side
for.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from src.extensions import db
from src.domains.network.connections.models.connection_request import (
    ConnectionEndReason,
    ConnectionInitiatorRole,
    ConnectionRequest,
    ConnectionRequestStatus,
)


class ConnectionRequestRepository:
    @staticmethod
    def get_for_business_and_supplier(
        business_id: str | UUID, supplier_profile_id: str | UUID
    ) -> Optional[ConnectionRequest]:
        return ConnectionRequest.query.filter_by(
            business_id=business_id, supplier_profile_id=supplier_profile_id, is_deleted=False
        ).first()

    @staticmethod
    def create(
        business_id: str | UUID,
        supplier_profile_id: str | UUID,
        initiated_by_role: ConnectionInitiatorRole = ConnectionInitiatorRole.BUSINESS,
    ) -> ConnectionRequest:
        """Concurrency-safe: every caller (request_connection,
        request_connection_to_business, complete_invitations_for_user)
        already checks get_for_business_and_supplier() first and only
        calls create() when nothing exists yet -- but that check-then-
        create pattern has a real race window between the check and
        this INSERT, proven by direct code inspection while building
        real concurrent-request tests (a live threaded server, ~10
        genuinely simultaneous calls at once — that specific run
        didn't trigger it, but "didn't happen to trigger it once" is
        not the same as "safe", so this is fixed regardless of what
        that one run showed).

        uq_connection_requests_business_supplier is what actually
        prevents a real duplicate row from ever being written; this
        just makes losing that race a normal, handled outcome (return
        whichever row actually won) instead of an unhandled 500."""
        request = ConnectionRequest(
            business_id=business_id,
            supplier_profile_id=supplier_profile_id,
            status=ConnectionRequestStatus.PENDING,
            initiated_by_role=initiated_by_role,
        )
        db.session.add(request)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            winner = ConnectionRequest.query.filter_by(
                business_id=business_id, supplier_profile_id=supplier_profile_id, is_deleted=False
            ).first()
            if winner is None:
                # The unique constraint fired for some OTHER reason
                # than the exact race this is designed for -- re-raise
                # rather than silently returning nothing, since that
                # would hide a genuinely different problem.
                raise
            return winner
        return request

    @staticmethod
    def list_pending_for_supplier_profile(supplier_profile_id: str | UUID) -> List[ConnectionRequest]:
        """BUSINESS-initiated only -- see this module's own docstring."""
        return (
            ConnectionRequest.query.filter_by(
                supplier_profile_id=supplier_profile_id,
                status=ConnectionRequestStatus.PENDING,
                initiated_by_role=ConnectionInitiatorRole.BUSINESS,
                is_deleted=False,
            )
            .order_by(ConnectionRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def list_pending_for_business(business_id: str | UUID) -> List[ConnectionRequest]:
        """SUPPLIER-initiated only -- the mirror of
        list_pending_for_supplier_profile, see this module's own
        docstring."""
        return (
            ConnectionRequest.query.filter_by(
                business_id=business_id,
                status=ConnectionRequestStatus.PENDING,
                initiated_by_role=ConnectionInitiatorRole.SUPPLIER,
                is_deleted=False,
            )
            .order_by(ConnectionRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id_and_supplier_profile(
        request_id: str | UUID, supplier_profile_id: str | UUID
    ) -> Optional[ConnectionRequest]:
        return ConnectionRequest.query.filter_by(
            id=request_id, supplier_profile_id=supplier_profile_id, is_deleted=False
        ).first()

    @staticmethod
    def get_by_id_and_business(request_id: str | UUID, business_id: str | UUID) -> Optional[ConnectionRequest]:
        return ConnectionRequest.query.filter_by(id=request_id, business_id=business_id, is_deleted=False).first()

    @staticmethod
    def set_status(request: ConnectionRequest, status: ConnectionRequestStatus) -> ConnectionRequest:
        request.status = status
        db.session.commit()
        return request

    @staticmethod
    def get_for_business_and_supplier_locked(
        business_id: str | UUID, supplier_profile_id: str | UUID
    ) -> Optional[ConnectionRequest]:
        """Same fetch as get_for_business_and_supplier, but row-locked
        (SELECT ... FOR UPDATE) -- used ONLY by the retry-after-decline
        path, where the service layer needs to check eligibility
        (daily/weekly limits) and then act on that SAME, unchanged
        state without a race window opening between the two. Not used
        for ordinary reads -- locking every read would be unnecessary
        overhead this domain's read-heavy paths (search, profile
        previews) don't need."""
        return (
            ConnectionRequest.query.filter_by(
                business_id=business_id, supplier_profile_id=supplier_profile_id, is_deleted=False
            )
            .with_for_update()
            .first()
        )

    @staticmethod
    def retry(request: ConnectionRequest, initiated_by_role: ConnectionInitiatorRole, attempted_at) -> ConnectionRequest:
        """Resets a DECLINED request back to PENDING and records this
        attempt in retry_history. Caller must already hold this row's
        lock (get_for_business_and_supplier_locked above) -- WHETHER
        this retry is allowed (the daily/weekly limits) is the
        SERVICE layer's decision, not this repository's; this method
        only performs the state change once that decision has already
        been made."""
        request.status = ConnectionRequestStatus.PENDING
        request.initiated_by_role = initiated_by_role
        request.retry_history = [*request.retry_history, attempted_at]
        db.session.commit()
        return request

    @staticmethod
    def reconnect(request: ConnectionRequest, initiated_by_role: ConnectionInitiatorRole) -> ConnectionRequest:
        """Resets an ENDED request back to PENDING -- a REAL BUG FOUND
        after direct report: request_connection's own
        _handle_existing_connection only ever special-cased DECLINED;
        every other non-PENDING/ACTIVE status (including ENDED) fell
        through to a silent no-op that returned the stale status
        without ever actually creating a new pending state. A business
        disconnecting from a supplier and then either side trying to
        reconnect would get a 200 response with nothing actually
        happening -- exactly matching the reported symptom ("backend
        is fine, it's just not appearing... on both roles").

        Deliberately its own method, NOT retry() above -- retry_history
        exists specifically for the DECLINED rate-limit mechanism;
        recording a reconnect-after-ENDED attempt there would silently
        pollute that history with an unrelated event, and could
        incorrectly count toward a FUTURE decline's own retry limit.
        No rate limiting here at all -- ending a connection is a
        voluntary action, not an adversarial rejection, so the same
        "guard against harassment" reasoning DECLINED's own retry path
        needs doesn't apply.

        Clears ended_reason/ended_details -- no longer relevant once a
        new connection attempt is underway; a future disconnect (if it
        happens again) will set its own fresh reason."""
        request.status = ConnectionRequestStatus.PENDING
        request.initiated_by_role = initiated_by_role
        request.ended_reason = None
        request.ended_details = None
        db.session.commit()
        return request

    @staticmethod
    def list_active_for_business(business_id: str | UUID) -> List[ConnectionRequest]:
        """ACTIVE only -- for the Community tab's "My Connections",
        regardless of which side originally initiated the request.
        Most-recently-connected first."""
        return (
            ConnectionRequest.query.filter_by(
                business_id=business_id, status=ConnectionRequestStatus.ACTIVE, is_deleted=False
            )
            .order_by(ConnectionRequest.updated_at.desc())
            .all()
        )

    @staticmethod
    def list_ended_for_business(business_id: str | UUID) -> List[ConnectionRequest]:
        """ENDED only -- the "who have I disconnected from" list. Same
        shape as list_active_for_business above, deliberately a
        SEPARATE method rather than a status parameter bolted onto
        that one -- that method already has a real, narrow, tested
        contract (ACTIVE only); overloading it risks every existing
        caller needing to account for a new parameter it never asked
        for. Most-recently-ended first, matching the same "most recent
        first" convention."""
        return (
            ConnectionRequest.query.filter_by(
                business_id=business_id, status=ConnectionRequestStatus.ENDED, is_deleted=False
            )
            .order_by(ConnectionRequest.updated_at.desc())
            .all()
        )

    @staticmethod
    def end_connection(
        connection: ConnectionRequest, reason: ConnectionEndReason, details: Optional[str]
    ) -> ConnectionRequest:
        """Transitions the SAME row ACTIVE -> ENDED -- never deleted,
        never replaced with a new row. See ConnectionRequestStatus's
        own docstring on ENDED for why."""
        connection.status = ConnectionRequestStatus.ENDED
        connection.ended_reason = reason
        connection.ended_details = details
        db.session.commit()
        return connection

    @staticmethod
    def list_active_for_supplier_profile(supplier_profile_id: str | UUID) -> List[ConnectionRequest]:
        """Mirrors list_active_for_business exactly, supplier side."""
        return (
            ConnectionRequest.query.filter_by(
                supplier_profile_id=supplier_profile_id, status=ConnectionRequestStatus.ACTIVE, is_deleted=False
            )
            .order_by(ConnectionRequest.updated_at.desc())
            .all()
        )
