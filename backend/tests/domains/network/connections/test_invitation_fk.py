"""
Tests for network_invitations.invited_user_id's ON DELETE SET NULL
fix -- a real bug found while building the expired-invitation cleanup
job: the existing auth account-cleanup job (7-day window) and the
invitation ticket's own default expiry (also 7 days) meant the
cleanup job's bulk DELETE would fail with a foreign key violation for
anyone who registered via a real invite and never verified. See
migration 2ea418343d1b_network_invitation_fk_set_null.py for the full
account.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.domains.auth.models.user import User
from src.domains.network.connections.models.network_invitation import (
    InvitationStatus,
    InvitedRole,
    NetworkInvitation,
)
from src.shared.tickets.tickets import create_ticket, hash_ticket


def test_deleting_a_referenced_user_sets_invitation_link_to_null_not_error(
    make_business, make_user, db_session
):
    """The exact scenario that used to raise a ProgrammingError: a
    User row still referenced by a REGISTERED invitation's
    invited_user_id gets bulk-deleted, matching exactly what
    auth/jobs/cleanup_unverified_emails.py does.

    Uses raw make_user (UNVERIFIED, no SupplierProfile) rather than
    make_supplier -- that fixture auto-seeds a SupplierProfile to
    mirror the REAL system's own invariant (a profile only ever exists
    for an ALREADY-VERIFIED account, see otp_service.py's
    _seed_supplier_profile). An abandoned, never-verified registrant
    can never actually have a profile in the real system, so giving
    this test one would test a combination that can't really happen
    -- and would trip a SEPARATE, unrelated foreign key
    (supplier_profiles_supplier_id_fkey) that has nothing to do with
    the fix this test is actually about."""
    from src.domains.auth.models.user import UserRole, VerificationStatus

    business = make_business()
    abandoned_registrant = make_user(
        "abandoned-fk@example.com", role=UserRole.SUPPLIER, verification_status=VerificationStatus.UNVERIFIED
    )
    db_session.commit()

    invitation = NetworkInvitation(
        inviter_id=business.id,
        invited_role=InvitedRole.SUPPLIER,
        invited_email="abandoned-fk@example.com",
        ticket_hash=hash_ticket(create_ticket()),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        status=InvitationStatus.REGISTERED,
        invited_user_id=abandoned_registrant.id,
    )
    db_session.add(invitation)
    db_session.commit()
    invitation_id = invitation.id  # captured BEFORE the delete below --
    # SQLAlchemy correctly expires ORM object attribute access after a
    # commit; touching invitation.id again afterward would trip its
    # own (correct) staleness detection, unrelated to the thing this
    # test is actually proving.

    # The exact operation the real cleanup job performs — must not raise.
    User.query.filter(User.id == abandoned_registrant.id).delete(synchronize_session=False)
    db_session.commit()

    surviving = NetworkInvitation.query.filter_by(id=invitation_id).first()
    assert surviving is not None
    assert surviving.invited_user_id is None
