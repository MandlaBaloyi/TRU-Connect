"""
Tests for the expired-invitation cleanup job
(jobs/expired_invitations_cleanup_job.py).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.domains.network.connections.jobs import expired_invitations_cleanup_job
from src.domains.network.connections.models.network_invitation import (
    InvitationStatus,
    InvitedRole,
    NetworkInvitation,
)
from src.extensions import db
from src.shared.tickets.tickets import create_ticket, hash_ticket


def _make_invitation(business, *, email, status, expires_delta):
    invitation = NetworkInvitation(
        inviter_id=business.id,
        invited_role=InvitedRole.SUPPLIER,
        invited_email=email,
        ticket_hash=hash_ticket(create_ticket()),
        expires_at=datetime.now(timezone.utc) + expires_delta,
        status=status,
    )
    db.session.add(invitation)
    db.session.commit()
    return invitation


def test_deletes_expired_pending_invitations(make_business, db_session):
    business = make_business()
    expired = _make_invitation(
        business, email="expired-job@example.com", status=InvitationStatus.PENDING, expires_delta=timedelta(days=-1)
    )
    expired_id = expired.id  # captured before run() deletes the row

    result = expired_invitations_cleanup_job.run()

    assert result.success is True
    assert result.count == 1
    assert NetworkInvitation.query.filter_by(id=expired_id).first() is None


def test_does_not_delete_unexpired_pending_invitations(make_business, db_session):
    business = make_business()
    fresh = _make_invitation(
        business, email="fresh-job@example.com", status=InvitationStatus.PENDING, expires_delta=timedelta(days=6)
    )
    fresh_id = fresh.id

    result = expired_invitations_cleanup_job.run()

    assert result.count == 0
    assert NetworkInvitation.query.filter_by(id=fresh_id).first() is not None


def test_does_not_delete_expired_registered_invitations(make_business, make_supplier, db_session):
    """REGISTERED (someone already used the ticket) is out of scope
    for this job -- see its own docstring on why: the account, not
    the invitation, is what needs cleaning up, and that's a different
    job's responsibility."""
    business = make_business()
    supplier_user = make_supplier("registered-job@example.com")
    invitation = _make_invitation(
        business, email="registered-job@example.com", status=InvitationStatus.REGISTERED, expires_delta=timedelta(days=-1)
    )
    invitation.invited_user_id = supplier_user.id
    db.session.commit()
    invitation_id = invitation.id

    result = expired_invitations_cleanup_job.run()

    assert result.count == 0
    assert NetworkInvitation.query.filter_by(id=invitation_id).first() is not None


def test_does_not_delete_expired_completed_invitations(make_business, db_session):
    business = make_business()
    completed = _make_invitation(
        business, email="completed-job@example.com", status=InvitationStatus.COMPLETED, expires_delta=timedelta(days=-1)
    )
    completed_id = completed.id

    result = expired_invitations_cleanup_job.run()

    assert result.count == 0
    assert NetworkInvitation.query.filter_by(id=completed_id).first() is not None


def test_processes_multiple_businesses_in_one_run(make_business, db_session):
    business_a = make_business("job-biz-a@example.com")
    business_b = make_business("job-biz-b@example.com")
    _make_invitation(business_a, email="a1@example.com", status=InvitationStatus.PENDING, expires_delta=timedelta(days=-1))
    _make_invitation(business_b, email="b1@example.com", status=InvitationStatus.PENDING, expires_delta=timedelta(days=-2))

    result = expired_invitations_cleanup_job.run()

    assert result.count == 2
