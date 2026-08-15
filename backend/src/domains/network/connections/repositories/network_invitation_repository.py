"""
NetworkInvitation repository -- ONLY talks to SQLAlchemy, no business
rules (same rule as every other repository in this codebase).

get_by_ticket_hash is the lookup-by-hash pattern
src.shared.tickets.tickets's own module docstring specifically calls
out as the safe one (an indexed equality lookup, not a fetch-then-
compare) -- same as PasswordResetRepository.get_by_token_hash.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.extensions import db
from src.domains.network.connections.models.network_invitation import (
    InvitationStatus,
    InvitedRole,
    NetworkInvitation,
)


class NetworkInvitationRepository:
    @staticmethod
    def create(
        inviter_id: str | UUID, invited_role: InvitedRole, invited_email: str, ticket_hash: str, expires_at
    ) -> NetworkInvitation:
        invitation = NetworkInvitation(
            inviter_id=inviter_id,
            invited_role=invited_role,
            invited_email=invited_email,
            ticket_hash=ticket_hash,
            expires_at=expires_at,
            status=InvitationStatus.PENDING,
        )
        db.session.add(invitation)
        db.session.commit()
        return invitation

    @staticmethod
    def get_by_ticket_hash(ticket_hash: str) -> Optional[NetworkInvitation]:
        return NetworkInvitation.query.filter_by(ticket_hash=ticket_hash, is_deleted=False).first()

    @staticmethod
    def get_pending_by_invited_user(invited_user_id: str | UUID) -> List[NetworkInvitation]:
        """Every REGISTERED (not yet COMPLETED) invitation linked to
        this user -- normally exactly one, but nothing stops an
        inviter from re-inviting before the first invite completes, so
        this returns all of them; the caller (OTP verification
        success) completes every one it finds, not just the first."""
        return NetworkInvitation.query.filter_by(
            invited_user_id=invited_user_id, status=InvitationStatus.REGISTERED, is_deleted=False
        ).all()

    @staticmethod
    def mark_registered(invitation: NetworkInvitation, invited_user_id: str | UUID) -> NetworkInvitation:
        invitation.status = InvitationStatus.REGISTERED
        invitation.invited_user_id = invited_user_id
        db.session.commit()
        return invitation

    @staticmethod
    def mark_completed(invitation: NetworkInvitation) -> NetworkInvitation:
        invitation.status = InvitationStatus.COMPLETED
        db.session.commit()
        return invitation
