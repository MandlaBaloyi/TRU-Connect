"""
Setting what a supplier pays for.

THE COLUMN EXISTED AND NOTHING COULD WRITE IT. plan_tier has been on
SupplierProfile since the tier work, with server_default FREE, and
until now no CLI command, no admin route and no service anywhere in
src/ ever set it -- so the entire V2_16 ladder was real in code and
unreachable in the product. The only MAX rows in the dev database were
put there by a seed script.

WHY A SERVICE AND NOT A COLUMN UPDATE IN THE CLI. The rule in
src/cli/__init__.py is explicit: commands call the SERVICE layer, never
raw SQL, because "a human changing rows by hand with no trail is how
you end up unable to answer 'who approved this, and when'". A plan is
exactly the kind of thing that gets asked about -- by the supplier
being billed, or by the one who believes a competitor was given
something they were not.

WHAT THIS IS NOT:

  NOT BILLING. Nothing here takes money, checks whether money was
  taken, or knows what a plan costs. V2_16's prices are explicitly
  placeholders for modelling. This records a DECISION; when a payment
  rail exists it will call this same function, and the audit line will
  simply have a payment reference in its metadata.

  NOT A PERMISSION. A FREE supplier who is verified is findable,
  orderable and appears in every earned rail their stock belongs in. A
  tier buys reach BEYOND what you have earned; it cannot buy the right
  to exist and it cannot buy another supplier's absence. Nothing here
  touches verification_status, and the two must never be confused --
  the curtain is about safety, this is about reach.

  NOT THE PLACE THAT DECIDES WHAT A TIER DOES. That is
  network/community/placement/tier_rules.py, and it stays there. This
  module writes a value; that one reads it and is the only thing
  allowed to have an opinion about what it means.

EXPIRY IS THE WHOLE REASON effective_tier EXISTS. A PARTNER agreement
or a trial is time-boxed, and tier_rules.effective_tier already treats
an expired plan as FREE on read -- so reach stops the moment the clock
runs out rather than whenever a nightly job next notices. Setting an
expiry here is therefore safe by construction; forgetting to set one on
a negotiated deal is the real hazard, which is why the CLI asks.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.core.exceptions import NotFoundError, ValidationError
from src.core.base_model import utcnow
from src.domains.supplier.supplier_profile.models.supplier_profile import (
    SupplierPlanTier,
    SupplierProfile,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.extensions import db


def set_plan(
    supplier_id,
    *,
    tier: str,
    decided_by_user_id: str,
    reason: str,
    expires_at: Optional[datetime] = None,
) -> SupplierProfile:
    """Put this supplier on a plan, and record who decided.

    A REASON IS REQUIRED, exactly as it is for verification. A record
    saying a supplier was moved to MAX by somebody for reasons nobody
    wrote down is worthless in three months, and three months is when
    it gets asked about.
    """
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Say why this plan changed — the record is the point.")

    try:
        wanted = SupplierPlanTier(tier.strip().upper())
    except (ValueError, AttributeError):
        allowed = ", ".join(t.value for t in SupplierPlanTier)
        raise ValidationError(f"{tier} is not a plan. Choose one of: {allowed}.")

    if expires_at is not None and expires_at <= utcnow():
        # REFUSED RATHER THAN ACCEPTED-AND-IGNORED. effective_tier reads
        # an expired plan as FREE, so this would silently do nothing at
        # all -- the command would report success and the supplier's
        # reach would not move. A typo in a date is the likeliest cause.
        raise ValidationError("That expiry is already in the past, so the plan would never apply.")

    # GETS THE PROFILE UNGATED, on purpose. Staff act on suppliers
    # whatever the curtain says about them -- an UNVERIFIED supplier can
    # perfectly well have negotiated a plan that starts the day they are
    # approved, and get_visible_by_id would hide them from the person
    # doing the approving.
    profile = SupplierProfileRepository.get_by_supplier_id(supplier_id)
    if profile is None:
        raise NotFoundError("That supplier has no profile yet.")

    was = profile.plan_tier
    was_expiry = profile.plan_expires_at

    profile.plan_tier = wanted
    # ALWAYS ASSIGNED, never left alone. Moving somebody from a
    # time-boxed PARTNER deal to FREE and leaving last year's expiry on
    # the row means the next person to read it cannot tell whether the
    # plan lapsed or was changed.
    profile.plan_expires_at = expires_at
    db.session.commit()

    _record(profile, decided_by_user_id, reason, was=was, was_expiry=was_expiry)
    return profile


def _record(profile, decided_by_user_id, reason, *, was, was_expiry) -> None:
    """Write the decision to the audit trail.

    NEVER RAISES, matching verification_service._record: the change is
    already committed, and an unreachable audit backend must not report
    failure for work that really happened. A missing audit line is a
    gap; a plan change that silently did not apply is a supplier
    wondering why they are paying for nothing.

    THE ACTOR IS THE DECIDER, NOT THE SUBJECT. The supplier being
    decided about goes in metadata -- the other way round produces a
    trail that reads as though suppliers grant themselves reach.
    """
    try:
        from src.shared.audit.audit import publish
        from src.shared.audit.audit_types import ActorType, AuditDomain, AuditEvent, AuditStatus
        from src.shared.audit.event_types import SupplierAuditEvent

        publish(
            AuditEvent(
                event_name=SupplierAuditEvent.PLAN_CHANGED,
                domain=AuditDomain.SUPPLIER,
                status=AuditStatus.SUCCESS,
                module="plan_service",
                actor_type=ActorType.ADMIN,
                user_id=decided_by_user_id,
                metadata={
                    "supplier_id": str(profile.supplier_id),
                    "business_name": profile.business_name,
                    "from_tier": getattr(was, "value", was),
                    "to_tier": profile.plan_tier.value if profile.plan_tier else None,
                    "from_expires_at": was_expiry.isoformat() if was_expiry else None,
                    "to_expires_at": (
                        profile.plan_expires_at.isoformat() if profile.plan_expires_at else None
                    ),
                    "reason": reason,
                    "source": "CLI",
                },
            )
        )
    except Exception:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).exception("plan_service: failed to write an audit event")
