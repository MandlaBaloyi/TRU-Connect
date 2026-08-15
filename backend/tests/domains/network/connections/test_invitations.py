"""
Network Invitation service-layer tests -- file.txt Phase 2 /
FILE2.txt "PHASE 2 -- SUPPLIER INVITATION", GENERALIZED to both
directions. Full HTTP-level bidirectional lifecycle proof (both
business->supplier and supplier->business, including invite->
register-with-ticket->verify->auto-PENDING-relationship->approve) was
run manually against real Postgres before being written down here --
these tests cover the same behaviour at the service layer, plus edge
cases (expiry, double-completion) not exercised in that manual run.
"""
from __future__ import annotations

from src.domains.network.connections.models.connection_request import ConnectionRequest
from src.domains.network.connections.models.network_invitation import InvitationStatus, InvitedRole, NetworkInvitation
from src.domains.network.connections.repositories.network_invitation_repository import (
    NetworkInvitationRepository,
)
from src.domains.network.connections.services import connections_service
from src.shared.email.email import get_fake_provider
from src.shared.tickets.tickets import create_ticket, hash_ticket, ticket_expiry


def test_invite_supplier_creates_pending_invitation(make_business, db_session):
    business = make_business()
    get_fake_provider().clear()

    connections_service.invite_supplier(business.id, "invitee@example.com")

    invitation = NetworkInvitation.query.filter_by(inviter_id=business.id).first()
    assert invitation is not None
    assert invitation.invited_email == "invitee@example.com"
    assert invitation.invited_role == InvitedRole.SUPPLIER
    assert invitation.status == InvitationStatus.PENDING


def test_invite_business_creates_pending_invitation(make_supplier, db_session):
    supplier_user = make_supplier()
    get_fake_provider().clear()

    connections_service.invite_business(supplier_user.id, "invitee-biz@example.com")

    invitation = NetworkInvitation.query.filter_by(inviter_id=supplier_user.id).first()
    assert invitation is not None
    assert invitation.invited_email == "invitee-biz@example.com"
    assert invitation.invited_role == InvitedRole.BUSINESS
    assert invitation.status == InvitationStatus.PENDING


def test_invite_supplier_sends_real_email(make_business):
    business = make_business()
    get_fake_provider().clear()

    connections_service.invite_supplier(business.id, "invitee2@example.com")

    sent = [e for e in get_fake_provider().sent_emails if e["to"] == "invitee2@example.com"]
    assert len(sent) == 1
    assert "invited you" in sent[0]["subject"]


def test_invite_business_sends_real_email(make_supplier):
    supplier_user = make_supplier()
    get_fake_provider().clear()

    connections_service.invite_business(supplier_user.id, "invitee-biz2@example.com")

    sent = [e for e in get_fake_provider().sent_emails if e["to"] == "invitee-biz2@example.com"]
    assert len(sent) == 1
    assert "invited you" in sent[0]["subject"]


def test_validate_invitation_true_for_fresh_ticket(make_business):
    business = make_business()
    get_fake_provider().clear()

    connections_service.invite_supplier(business.id, "fresh@example.com")
    sent = [e for e in get_fake_provider().sent_emails if e["to"] == "fresh@example.com"][0]
    import re

    ticket = re.search(r"ticket=([\w-]+)", sent["html_body"]).group(1)

    assert connections_service.validate_invitation(ticket) is True


def test_validate_invitation_false_for_unknown_ticket(app):
    assert connections_service.validate_invitation("not-a-real-ticket") is False


def test_validate_invitation_false_for_expired_ticket(make_business, db_session):
    business = make_business()
    raw = create_ticket()
    NetworkInvitationRepository.create(
        inviter_id=business.id,
        invited_role=InvitedRole.SUPPLIER,
        invited_email="expired@example.com",
        ticket_hash=hash_ticket(raw),
        expires_at=ticket_expiry(hours=-1),  # already in the past
    )
    assert connections_service.validate_invitation(raw) is False


def test_link_invitation_at_registration_moves_to_registered(make_business, make_supplier, db_session):
    business = make_business()
    raw = create_ticket()
    NetworkInvitationRepository.create(
        inviter_id=business.id,
        invited_role=InvitedRole.SUPPLIER,
        invited_email="link-test@example.com",
        ticket_hash=hash_ticket(raw),
        expires_at=ticket_expiry(hours=1),
    )
    new_supplier = make_supplier("link-test@example.com")

    connections_service.link_invitation_at_registration(raw, new_supplier.id, "supplier")

    invitation = NetworkInvitationRepository.get_by_ticket_hash(hash_ticket(raw))
    assert invitation.status == InvitationStatus.REGISTERED
    assert invitation.invited_user_id == new_supplier.id


def test_link_invitation_ignores_role_mismatch(make_business, make_supplier, db_session):
    """A ticket meant for a future SUPPLIER must not link if someone
    registers as a BUSINESS with it -- see
    link_invitation_at_registration's own docstring on why this is a
    silent no-op, not an error."""
    business = make_business()
    raw = create_ticket()
    NetworkInvitationRepository.create(
        inviter_id=business.id,
        invited_role=InvitedRole.SUPPLIER,
        invited_email="mismatch@example.com",
        ticket_hash=hash_ticket(raw),
        expires_at=ticket_expiry(hours=1),
    )
    wrong_role_user = make_business("mismatch-registrant@example.com")

    connections_service.link_invitation_at_registration(raw, wrong_role_user.id, "business")

    invitation = NetworkInvitationRepository.get_by_ticket_hash(hash_ticket(raw))
    assert invitation.status == InvitationStatus.PENDING  # untouched
    assert invitation.invited_user_id is None


def test_link_invitation_silently_ignores_invalid_ticket(make_supplier, db_session):
    """A stale/garbage ticket at registration must never raise -- see
    connections_service.link_invitation_at_registration's own
    docstring: this is a silent no-op by design."""
    new_supplier = make_supplier("noop@example.com")
    connections_service.link_invitation_at_registration(
        "garbage-ticket", new_supplier.id, "supplier"
    )  # must not raise


def test_complete_invitations_creates_connection_request(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier("complete-test@example.com")
    profile = make_supplier_profile(supplier_user, business_name="Complete Test Co")

    raw = create_ticket()
    NetworkInvitationRepository.create(
        inviter_id=business.id,
        invited_role=InvitedRole.SUPPLIER,
        invited_email="complete-test@example.com",
        ticket_hash=hash_ticket(raw),
        expires_at=ticket_expiry(hours=1),
    )
    connections_service.link_invitation_at_registration(raw, supplier_user.id, "supplier")

    assert ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).count() == 0

    connections_service.complete_invitations_for_user(supplier_user.id, "supplier")

    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert request is not None
    assert request.status.value.upper() == "PENDING"
    assert request.initiated_by_role.value.upper() == "BUSINESS"

    invitation = NetworkInvitationRepository.get_by_ticket_hash(hash_ticket(raw))
    assert invitation.status == InvitationStatus.COMPLETED


def test_complete_invitations_reverse_direction(make_business, make_supplier, make_supplier_profile):
    """Supplier invites a business -- the just-verified BUSINESS
    becomes business_id, the INVITER (a supplier) resolves to
    supplier_profile_id, and initiated_by_role is SUPPLIER."""
    supplier_user = make_supplier("inviter-supplier@example.com")
    profile = make_supplier_profile(supplier_user, business_name="Inviter Supplier Co")

    raw = create_ticket()
    NetworkInvitationRepository.create(
        inviter_id=supplier_user.id,
        invited_role=InvitedRole.BUSINESS,
        invited_email="new-business@example.com",
        ticket_hash=hash_ticket(raw),
        expires_at=ticket_expiry(hours=1),
    )
    new_business = make_business("new-business@example.com")
    connections_service.link_invitation_at_registration(raw, new_business.id, "business")

    connections_service.complete_invitations_for_user(new_business.id, "business")

    request = ConnectionRequest.query.filter_by(business_id=new_business.id, supplier_profile_id=profile.id).first()
    assert request is not None
    assert request.status.value.upper() == "PENDING"
    assert request.initiated_by_role.value.upper() == "SUPPLIER"


def test_completing_twice_does_not_duplicate_connection_request(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier("double-complete@example.com")
    profile = make_supplier_profile(supplier_user, business_name="Double Complete Co")

    raw = create_ticket()
    NetworkInvitationRepository.create(
        inviter_id=business.id,
        invited_role=InvitedRole.SUPPLIER,
        invited_email="double-complete@example.com",
        ticket_hash=hash_ticket(raw),
        expires_at=ticket_expiry(hours=1),
    )
    connections_service.link_invitation_at_registration(raw, supplier_user.id, "supplier")

    connections_service.complete_invitations_for_user(supplier_user.id, "supplier")
    # A second call must be a no-op -- the invitation is already
    # COMPLETED, so get_pending_by_invited_user (REGISTERED-only) won't
    # even find it a second time.
    connections_service.complete_invitations_for_user(supplier_user.id, "supplier")

    count = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).count()
    assert count == 1
