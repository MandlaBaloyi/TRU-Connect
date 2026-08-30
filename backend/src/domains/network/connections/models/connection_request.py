"""
ConnectionRequest -- the minimal Phase 1 slice of the future
supplier_customer_relationship domain (file.txt Phase 2/3;
FILE2.txt's own "PHASE 2 -- SUPPLIER CONNECTION REQUEST"). Deliberately
NOT the full relationship state machine (PENDING/ACTIVE/DECLINED/
SUSPENDED/TERMINATED + approval flow) -- this round only needs to
honestly back "a business requested a connection", nothing past that.
Approval (Phase 3) adds the transitions this model doesn't have yet;
extending status's enum + a supplier-side approve/decline service call
is the expected next step, not a redesign of this table.

Lives in network/connections (not business/ or supplier/ alone)
because the relationship belongs to both sides equally -- same
reasoning as this domain's own placement at the top level, alongside
security/platform/trust.

initiated_by_role -- GENERALIZATION: originally every request was
business-initiated (Find Supplier), so there was only ever one
approval direction (supplier approves). Now that a supplier can
initiate a request too (the reverse Find Business flow), the system
needs to know WHICH side owes the approval -- a business-initiated
row surfaces on the supplier's Customer Requests; a supplier-initiated
row surfaces on the business's own (new) Supplier Requests. Without
this column there would be no way to tell the two apart once both
directions exist.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import ARRAY, UUID

from src.core.base_model import BaseModel
from src.extensions import db


class ConnectionRequestStatus(str, enum.Enum):
    """Only PENDING is reachable by any code path this round --
    ACTIVE/DECLINED are modelled now so Phase 3's supplier-approval
    service extends this same table/enum instead of migrating it
    again, matching the frontend's own types.ts ConnectionStatus,
    which already models the full future set for the identical reason.

    ENDED added later -- a business voluntarily disconnecting from an
    ACTIVE relationship, exactly the extension this docstring's own
    "extending status's enum... is the expected next step" already
    anticipated. The SAME row transitions ACTIVE -> ENDED rather than
    being deleted or replaced -- nothing in this codebase hard-deletes
    a real relationship's own history."""

    PENDING = "pending"
    ACTIVE = "active"
    DECLINED = "declined"
    ENDED = "ended"


class ConnectionEndReason(str, enum.Enum):
    """Why a business chose to end an ACTIVE connection -- same
    "preset reasons plus a genuine free-text escape hatch" shape as
    SupplierReportReason (see supplier_report.py), deliberately mirrored
    rather than invented separately, since both are "a business is
    telling us something went wrong with a supplier" moments."""

    FOUND_BETTER_SUPPLIER = "found_better_supplier"
    NO_LONGER_NEEDED = "no_longer_needed"
    BAD_EXPERIENCE = "bad_experience"
    OTHER = "other"


class ConnectionInitiatorRole(str, enum.Enum):
    """Which side created this request -- see this module's own
    docstring on why this exists."""

    BUSINESS = "business"
    SUPPLIER = "supplier"


class ConnectionRequest(BaseModel):
    __tablename__ = "connection_requests"
    __table_args__ = (
        # A business can have at most ONE non-superseded request per
        # supplier -- enforced here, not just assumed by the service,
        # so a race between two rapid double-taps can't create two
        # rows (see service layer's own idempotency handling for the
        # normal-path version of this same guarantee). Unique
        # regardless of which side initiated -- there is still only
        # ever one relationship between a given business and supplier.
        db.UniqueConstraint("business_id", "supplier_profile_id", name="uq_connection_requests_business_supplier"),
        db.Index("ix_connection_requests_business_id", "business_id"),
        db.Index("ix_connection_requests_supplier_profile_id", "supplier_profile_id"),
        {"schema": "network"},
    )

    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)
    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    status = db.Column(
        db.Enum(ConnectionRequestStatus, name="connection_request_status", schema="network"),
        nullable=False,
        default=ConnectionRequestStatus.PENDING,
    )
    initiated_by_role = db.Column(
        db.Enum(ConnectionInitiatorRole, name="connection_initiator_role", schema="network"),
        nullable=False,
        default=ConnectionInitiatorRole.BUSINESS,
    )
    # One timestamp per retry attempt after a DECLINED request -- see
    # migration c410a2f2aae9_connection_request_retry_history.py's own
    # docstring on why this is a real timestamp history, not a single
    # counter: only a per-attempt history can correctly tell "N
    # retries per day" from "M retries per week" (a plain counter
    # can't distinguish attempts an hour apart from attempts a week
    # apart). Empty list, never null -- see this column's own default.
    retry_history = db.Column(ARRAY(db.DateTime(timezone=True)), nullable=False, default=list)

    # Both null until a business actually ends an ACTIVE connection --
    # see ConnectionEndReason's own docstring. Kept on this same row
    # (not a separate table) since there's only ever one "ending" per
    # relationship's own lifetime at a time; if it's later reconnected
    # and ended again, that's a fresh transition on the same row,
    # overwriting these two fields with the new reason -- the row's
    # own updated_at (BaseModel) already tracks when that happened.
    ended_reason = db.Column(
        db.Enum(ConnectionEndReason, name="connection_end_reason", schema="network"), nullable=True
    )
    ended_details = db.Column(db.String(500), nullable=True)
