"""
Network Invitation -- file.txt Phase 2, GENERALIZED to both directions
(a business invites a supplier who isn't on TruConnect yet, or vice
versa).

TWO-STAGE LINKING: link_invitation_at_registration() runs from
AuthService.register_supplier / register_business at RAW registration
time -- but only ever links the invitation to the new (still-unverified)
account, it never creates a ConnectionRequest.
complete_invitations_for_user() runs from OTPService's verification-
success hook -- THAT'S where the real ConnectionRequest gets created.
See network_invitation.py's own docstring for why this split matters
(the hard-delete/orphan-FK reasoning).
"""
from __future__ import annotations

from uuid import UUID

from src.domains.network.connections.models.connection_request import ConnectionInitiatorRole
from src.domains.network.connections.repositories.connection_request_repository import (
    ConnectionRequestRepository,
)
from src.domains.network.connections.services._common import (
    _lookup_business_name,
    _lookup_supplier_name,
    _resolve_supplier_profile_id,
)
from src.shared.validation.identifiers import normalize_email


def invite_supplier(business_id: str | UUID, email: str) -> dict:
    from src.domains.network.connections.models.network_invitation import InvitedRole

    return _send_invitation(
        inviter_id=business_id,
        invited_role=InvitedRole.SUPPLIER,
        email=email,
        rate_limit_prefix="supplier_invitation",
        template_name="supplier/supplier_invitation.html",
        inviter_name_lookup=_lookup_business_name,
    )


def invite_business(supplier_id: str | UUID, email: str) -> dict:
    from src.domains.network.connections.models.network_invitation import InvitedRole

    return _send_invitation(
        inviter_id=supplier_id,
        invited_role=InvitedRole.BUSINESS,
        email=email,
        rate_limit_prefix="business_invitation",
        template_name="business/business_invitation.html",
        inviter_name_lookup=_lookup_supplier_name,
    )


def _send_invitation(
    inviter_id, invited_role, email: str, rate_limit_prefix: str, template_name: str, inviter_name_lookup
) -> dict:
    """Rate-limiting happens at the EMAIL layer (EmailService.send_template's
    own rate_limit_key/max), same as every other outbound email in this
    codebase -- not duplicated here."""
    from flask import current_app

    from src.domains.network.connections.repositories.network_invitation_repository import (
        NetworkInvitationRepository,
    )
    from src.shared.constants.constants import (
        DEFAULT_SUPPLIER_INVITATION_EXPIRY_HOURS,
        MAX_SUPPLIER_INVITATIONS_PER_HOUR,
    )
    from src.shared.email.email import EmailService
    from src.shared.tickets.tickets import create_ticket, hash_ticket, ticket_expiry

    normalized = normalize_email(email)

    expiry_hours = current_app.config.get(
        "SUPPLIER_INVITATION_EXPIRY_HOURS", DEFAULT_SUPPLIER_INVITATION_EXPIRY_HOURS
    )
    raw_ticket = create_ticket()
    expires_at = ticket_expiry(hours=expiry_hours)
    NetworkInvitationRepository.create(
        inviter_id=inviter_id,
        invited_role=invited_role,
        invited_email=normalized,
        ticket_hash=hash_ticket(raw_ticket),
        expires_at=expires_at,
    )

    inviter_name = inviter_name_lookup(inviter_id)
    base_url = current_app.config.get("APP_BASE_URL", "http://localhost:5000")
    invitation_url = f"{base_url}/join?ticket={raw_ticket}"

    EmailService.send_template(
        to=normalized,
        template_name=template_name,
        subject=f"{inviter_name} invited you to TruConnect",
        context={"inviter_business_name": inviter_name, "invitation_url": invitation_url},
        rate_limit_key=f"{rate_limit_prefix}:{inviter_id}",
        rate_limit_max=MAX_SUPPLIER_INVITATIONS_PER_HOUR,
        rate_limit_window_seconds=3600,
    )

    return {"status": "SENT"}


def link_invitation_at_registration(ticket: str, new_user_id: str | UUID, new_user_role: str) -> None:
    """Called from AuthService.register_supplier / register_business --
    registration time, NOT verification time. Silently no-ops for a
    missing/expired/already-used ticket, OR when the ticket's
    invited_role doesn't match the role actually being registered -- a
    mismatch here is a reason to skip the automatic linkage, never a
    reason to block someone from creating an account normally.
    """
    from src.domains.network.connections.repositories.network_invitation_repository import (
        NetworkInvitationRepository,
    )
    from src.shared.tickets.tickets import hash_ticket

    invitation = NetworkInvitationRepository.get_by_ticket_hash(hash_ticket(ticket))
    if invitation is None or not invitation.is_valid():
        return
    if invitation.invited_role.value != new_user_role:
        return
    NetworkInvitationRepository.mark_registered(invitation, new_user_id)


def complete_invitations_for_user(user_id: str | UUID, user_role: str) -> None:
    """Called from OTPService's verification-success hook. Never
    raises: a failure here must not block the account's actual,
    already-succeeded verification, same resilience rule the seed
    helpers follow (their caller wraps this in the same try/except).

    user_role determines which side of the ConnectionRequest the
    just-verified person becomes, and which side the ORIGINAL inviter
    was (always the complement) -- see network_invitation.py's own
    docstring.
    """
    from src.domains.network.connections.models.network_invitation import InvitedRole
    from src.domains.network.connections.repositories.network_invitation_repository import (
        NetworkInvitationRepository,
    )

    for invitation in NetworkInvitationRepository.get_pending_by_invited_user(user_id):
        if invitation.invited_role == InvitedRole.SUPPLIER:
            # A business invited a supplier -- the just-verified user
            # IS that supplier.
            supplier_profile_id = _resolve_supplier_profile_id(user_id)
            business_id = invitation.inviter_id
            initiator = ConnectionInitiatorRole.BUSINESS
        else:
            # A supplier invited a business -- the just-verified user
            # IS that business; the inviter is the supplier.
            supplier_profile_id = _resolve_supplier_profile_id(invitation.inviter_id)
            business_id = user_id
            initiator = ConnectionInitiatorRole.SUPPLIER

        existing = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
        if existing is None:
            ConnectionRequestRepository.create(business_id, supplier_profile_id, initiated_by_role=initiator)
        NetworkInvitationRepository.mark_completed(invitation)


def validate_invitation(ticket: str) -> bool:
    """Read-only check -- lets a registration screen reached via a
    deep link show "this invite has expired" immediately, before the
    person fills in a form. Mirrors PasswordResetService.validate_ticket
    exactly."""
    from src.domains.network.connections.repositories.network_invitation_repository import (
        NetworkInvitationRepository,
    )
    from src.shared.tickets.tickets import hash_ticket

    invitation = NetworkInvitationRepository.get_by_ticket_hash(hash_ticket(ticket))
    return invitation is not None and invitation.is_valid()
