"""
NetworkInvitation -- file.txt Phase 2 / FILE2.txt's "PHASE 2 -- SUPPLIER
INVITATION", GENERALIZED. Originally SupplierInvitation, built assuming
only "business invites a future supplier" -- renamed and extended here
to support the reverse direction too ("supplier invites a future
business"), since the underlying mechanism (secure ticket, register-
with-ticket, auto-link at verification) is identical either way. Doing
this rename now, while the table has almost no real data, avoids
carrying a misleadingly-named column forward indefinitely.

invited_role is the ONE new fact needed to support both directions:
what role the invited person becomes once they register. The
inviter's own role is always the COMPLEMENT of invited_role (a
business invites a future supplier, a supplier invites a future
business) -- there's no same-role invitation concept in this domain,
so a separate inviter_role column would just duplicate that
derivation.

TICKET STORAGE: ticket_hash is produced by src.shared.tickets.tickets
(hash_ticket) -- see that module's own docstring. Same reasoning as
PasswordResetToken: never store the raw ticket, only its hash.

TWO-STAGE LINKING, not one -- see services/invitation_service.py's
own docstring for the full reasoning, but in short: PENDING ->
REGISTERED happens at registration (someone used the ticket),
REGISTERED -> COMPLETED happens at OTP verification success. An
unverified account can still be hard-deleted by the existing cleanup
job (auth_service.py's _is_unverified_expired) -- creating the real
ConnectionRequest before verification would risk exactly the same
orphaned-reference problem the supplier-profile seed timing was chosen
to avoid.

invited_user_id is nullable and only set once someone actually
registers with this ticket. ON DELETE SET NULL (not the Postgres
default NO ACTION) -- a real bug found while building the expired-
invitation cleanup job: the existing auth account-cleanup job hard-
deletes abandoned unverified accounts after 7 days, the same window
as this ticket's own default expiry, so without SET NULL that delete
would fail outright with a foreign key violation for anyone who
registered via invite and never verified (see migration
2ea418343d1b_network_invitation_fk_set_null.py for the full account).
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class InvitationStatus(str, enum.Enum):
    PENDING = "pending"
    REGISTERED = "registered"
    COMPLETED = "completed"


class InvitedRole(str, enum.Enum):
    """What the invited person becomes once they register -- see this
    module's own docstring for why the inviter's role is never stored
    separately (it's always the complement)."""

    BUSINESS = "business"
    SUPPLIER = "supplier"


class NetworkInvitation(BaseModel):
    __tablename__ = "network_invitations"
    __table_args__ = (
        db.Index("ix_network_invitations_ticket_hash", "ticket_hash"),
        db.Index("ix_network_invitations_inviter_id", "inviter_id"),
        {"schema": "network"},
    )

    inviter_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)
    invited_role = db.Column(
        db.Enum(InvitedRole, name="invited_role", schema="network"),
        nullable=False,
    )
    # Normalized (shared.validation.identifiers.normalize_email) before
    # storage -- same convention as SupplierProfile.normalized_email,
    # for the eventual case someone re-invites the same address and
    # this needs to match reliably.
    invited_email = db.Column(db.String(255), nullable=False)
    ticket_hash = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(
        db.Enum(InvitationStatus, name="invitation_status", schema="network"),
        nullable=False,
        default=InvitationStatus.PENDING,
    )
    invited_user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("auth.users.id", ondelete="SET NULL"), nullable=True
    )

    def is_valid(self) -> bool:
        """Read-only check -- mirrors PasswordResetToken.is_valid()
        exactly. A REGISTERED (not yet COMPLETED) invitation is still
        "valid" in the sense that its ticket has already done its one
        real job (linking a user at registration); this method is
        about whether the ticket itself could still be legitimately
        presented, not whether the overall flow has finished."""
        from src.core.base_model import utcnow

        if self.status == InvitationStatus.COMPLETED:
            return False
        return self.expires_at > utcnow()
