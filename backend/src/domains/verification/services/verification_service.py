"""
Granting and revoking supplier verification.

PHASE 1 HOLDS NO DOCUMENTS AT ALL, and that is the point rather than a
shortcut. The curtain is what makes the platform safe; the document
pipeline is what makes verification scale. Building the curtain first
means the safety property is true today, with a manual switch, while
holding none of the personal data that makes a breach serious.

So a decision here is made by a human who looked at something
out-of-band -- a WhatsApp photo of a certificate, a phone call, a
person they know -- and recorded the outcome. V2_12 Phase 2 replaces
"looked at something out-of-band" with an intake pipeline and an
audited review queue. Nothing in this module's shape needs to change
when it does: the decision, the actor, the reason and the timestamp
are already the record.

WHY THE REASON IS MANDATORY. `flask verification approve <id>` with no
reason produces a row saying a supplier was verified by someone, for
reasons nobody wrote down. That is worthless three months later, and
three months later is exactly when somebody asks. The prompt is not
bureaucracy -- it is the entire evidential value of a manual decision.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.core.exceptions import NotFoundError, ValidationError
from src.domains.supplier.supplier_profile.models.supplier_profile import (
    SupplierProfile,
    SupplierVerificationStatus,
)
from src.core.base_model import utcnow
from src.extensions import db
from src.shared.audit.event_types import VerificationAuditEvent


def _get_profile(supplier_id) -> SupplierProfile:
    profile = SupplierProfile.query.filter_by(supplier_id=supplier_id, is_deleted=False).first()
    if profile is None:
        raise NotFoundError("No supplier profile for that account.")
    return profile


def get_status(supplier_id) -> dict:
    """What a supplier is told about their own state.

    DELIBERATELY PHRASED FOR THE SUPPLIER, not for us. V2_03 Part 4.5
    is explicit that the message is "your shop is ready and nobody can
    see it yet", never "you are not verified" -- the second reads as a
    scolding to someone who has just spent an hour building a
    catalogue, and it is also less accurate. Their work is real. It is
    the visibility that is pending.
    """
    from src.domains.verification.visibility import is_visible_to_buyers

    profile = _get_profile(supplier_id)
    visible = is_visible_to_buyers(profile)
    return {
        "status": profile.verification_status.value if profile.verification_status else None,
        "visibleToBuyers": visible,
        "headline": (
            "Your shop is live." if visible else "Your shop is ready — buyers cannot see it yet."
        ),
        "detail": (
            "Businesses can find you, browse your catalogue and place orders."
            if visible
            else (
                "Keep building: your catalogue, prices and settings are all saved. "
                "The day your business is verified, everything you have set up "
                "becomes visible at once."
            )
        ),
    }


def approve(supplier_id, *, decided_by_user_id: str, reason: str) -> SupplierProfile:
    """Open the curtain. The supplier becomes findable and sellable."""
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Say why this supplier was approved — the record is the point.")

    profile = _get_profile(supplier_id)
    was = profile.verification_status
    profile.verification_status = SupplierVerificationStatus.VERIFIED
    # CLEAN SLATE, so that if this supplier is ever revoked later the
    # ladder starts from that moment rather than from an account
    # created two years ago -- which would fire all three reminders in
    # the first sweep after the revocation.
    profile.verification_reminder_stage = 0
    profile.verification_reminder_sent_at = None
    db.session.commit()
    _record(
        profile, VerificationAuditEvent.SUPPLIER_APPROVED, decided_by_user_id, reason, was=was
    )
    _notify_approved(profile)
    return profile


def revoke(supplier_id, *, decided_by_user_id: str, reason: str) -> SupplierProfile:
    """Close the curtain again.

    BACK TO UNVERIFIED, NOT TO A NEW "REVOKED" STATE. A fourth status
    would have to be taught to every screen, every filter and every
    badge, to express something none of them need to distinguish: what
    matters to a buyer is that this supplier is not currently sellable.
    Why that is true belongs in the decision record, which is where it
    can carry a sentence instead of an enum value.

    THE SUPPLIER'S WORK IS UNTOUCHED. Products, prices, inventory,
    connections and orders all survive -- only visibility changes. A
    revocation is not a deletion, and treating it as one would punish a
    supplier for an administrative event.
    """
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Say why this supplier's verification was revoked.")

    profile = _get_profile(supplier_id)
    was = profile.verification_status
    profile.verification_status = SupplierVerificationStatus.UNVERIFIED
    # THE LADDER'S CLOCK RESTARTS HERE, not at account creation. Both
    # fields together mean "nothing sent yet, and the wait began now".
    profile.verification_reminder_stage = 0
    profile.verification_reminder_sent_at = utcnow()
    db.session.commit()
    _record(
        profile, VerificationAuditEvent.SUPPLIER_REVOKED, decided_by_user_id, reason, was=was
    )

    # NO EMAIL IS SENT ON REVOCATION, and this is a decision rather than
    # an omission -- one that was made, reversed, and is worth writing
    # down so nobody "fixes" it later.
    #
    # A revocation email was built and then removed. The case for it was
    # that a supplier whose shop goes dark with no explanation concludes
    # the platform is broken. The case against, which won: the supplier
    # is NOT actually in the dark -- Settings -> Supplier visibility
    # shows "your shop is ready, buyers cannot see it yet" the moment
    # they look -- and an unsolicited email about a decision we made,
    # whose real reason we will not put in writing, invites a reply we
    # cannot answer honestly in a template.
    #
    # THE RECORD IS THE AUDIT TRAIL, not the inbox. _record above keeps
    # who decided, when, why, and the status it moved from -- which is
    # what a regulator asking "why was this supplier removed" actually
    # needs, and it survives long after any email would have been
    # deleted.
    return profile


def _record(profile, event, decided_by_user_id: Optional[str], reason: str, was=None) -> None:
    """Write the decision to the audit trail.

    NEVER RAISES. The decision is already committed above; an audit
    backend being unreachable must not roll back a verification that
    has really happened, nor report failure for work that succeeded.
    A missing audit line is a gap. A verification that silently did not
    apply is a supplier wondering why their shop is still dark.

    THE ACTOR IS THE DECIDER, NOT THE SUBJECT. user_id here is the
    staff member who decided; the supplier being decided about goes in
    metadata. Getting that the wrong way round would produce an audit
    trail that reads as though suppliers verify themselves.
    """
    try:
        from src.shared.audit.audit import publish
        from src.shared.audit.audit_types import ActorType, AuditDomain, AuditEvent, AuditStatus

        publish(
            AuditEvent(
                event_name=event,
                domain=AuditDomain.VERIFICATION,
                status=AuditStatus.SUCCESS,
                module="verification_service",
                actor_type=ActorType.USER,
                user_id=decided_by_user_id,
                metadata={
                    "supplier_id": str(profile.supplier_id),
                    "business_name": profile.business_name,
                    "reason": reason,
                    "source": "CLI",
                    # THE TRANSITION, NOT JUST THE DESTINATION. "Became
                    # unverified" and "was never verified" are different
                    # facts, and a regulator asking why a supplier was
                    # removed is asking about the first one. Recording
                    # only the new status would lose that distinction
                    # permanently.
                    "from_status": was.value if was is not None else None,
                    "to_status": (
                        profile.verification_status.value
                        if profile.verification_status is not None
                        else None
                    ),
                },
            )
        )
    except Exception:  # noqa: BLE001
        pass


def _notify_approved(profile) -> None:
    """Tell the supplier their shop is live.

    NEVER RAISES, for the same reason _record does not: the decision is
    already committed. An unreachable mail server must not turn a
    verification that really happened into a command that reports
    failure, and EmailService.send_template swallows its own errors
    anyway -- this guard covers the lookup and rendering around it.

    APPROVAL ONLY. Revocation deliberately sends nothing -- see
    revoke() for that reasoning. This function takes no reason
    argument at all, so the internal note recorded against a decision
    cannot reach an inbox even by accident.
    """
    try:
        from src.domains.auth.repositories.user_repository import UserRepository
        from src.domains.verification.notification_templates import verification_emails
        from src.shared.email.email import EmailService

        user = UserRepository.get_by_id(profile.supplier_id)
        if user is None or not user.email:
            return

        template_name, subject, context = verification_emails.approved(user, profile)
        EmailService.send_template(
            to=user.email, template_name=template_name, subject=subject, context=context
        )
    except Exception:  # noqa: BLE001
        from flask import current_app

        current_app.logger.exception("verification: failed to send the approval email")


def list_by_status(status: Optional[SupplierVerificationStatus] = None, limit: int = 50):
    """Suppliers, newest first, optionally filtered by status -- what
    the CLI shows when deciding who is waiting."""
    query = SupplierProfile.query.filter(SupplierProfile.is_deleted.is_(False))
    if status is not None:
        query = query.filter(SupplierProfile.verification_status == status)
    return query.order_by(SupplierProfile.created_at.desc()).limit(limit).all()


def resolve_supplier(identifier: str) -> SupplierProfile:
    """Find a supplier by user id or by email, so a human never has to
    copy a UUID out of one terminal window into another."""
    from src.domains.auth.repositories.user_repository import UserRepository

    if "@" in identifier:
        user = UserRepository.get_by_email(identifier)
        if user is None:
            raise NotFoundError(f"No account with the email {identifier}.")
        return _get_profile(user.id)

    try:
        supplier_id = UUID(identifier)
    except (ValueError, AttributeError):
        raise NotFoundError(f"{identifier} is not an email address or a user id.")
    return _get_profile(supplier_id)
