"""
`flask plans ...` -- what a supplier pays for, and therefore their reach.

THE LADDER WAS UNREACHABLE. plan_tier has sat on SupplierProfile since
the tier work with server_default FREE, tier_rules has read it, the
sponsored slot has gated on it -- and nothing in src/ has ever written
it. The only MAX rows anywhere were put there by a seed script, which
means the whole of V2_16 was real in code and absent from the product.
These commands are the missing half.

SAME SHAPE AS `flask verification ...` ON PURPOSE. `show` and `list`
read, `set` writes, the write asks who you are and insists on a reason.
Somebody who has learned one of these vocabularies has learned both,
and a reviewer working two queues with one vocabulary makes fewer
mistakes than one learning two.

REACH, NOT PERMISSION, and the commands say so out loud where somebody
might confuse the two. A FREE supplier who is verified is findable,
orderable and appears in every earned rail their stock belongs in.
Verification is the curtain and is about safety; this is about reach.
Running `flask plans set` on an unverified supplier is allowed and does
nothing visible until somebody approves them -- which is the correct
behaviour for a deal negotiated before onboarding finished.

THE CAPABILITY IS supplier:plan, its own name rather than
supplier:verify. Deciding that a business is real and deciding what
they may pay for reach are different jobs, and one day they are
different people -- a salesperson who closes a PARTNER deal has no
business opening the curtain. Naming them apart costs nothing today and
is the thing that is expensive to retrofit.
"""
from __future__ import annotations

from datetime import datetime, timezone

import click
from flask.cli import AppGroup

from src.cli._shared.capabilities import SUPPLIER_PLAN

plans_cli = AppGroup("plans", help="Set and inspect supplier plans.")


def _tier_names() -> list:
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierPlanTier

    return [t.value for t in SupplierPlanTier]


def _effective(profile) -> str:
    """What tier_rules will ACTUALLY read for this supplier right now.

    SHOWN ALONGSIDE THE STORED VALUE, never instead of it. A row saying
    PARTNER that behaves as FREE because the agreement lapsed last
    Tuesday is the single most confusing state this feature has, and
    printing only one of the two numbers guarantees somebody debugs the
    wrong one.
    """
    from src.domains.network.community.placement import tier_rules

    return tier_rules.effective_tier(profile)


@plans_cli.command("show")
@click.argument("identifier")
def show(identifier: str) -> None:
    """One supplier's plan, by email or user id."""
    from src.domains.network.community.placement import tier_rules
    from src.domains.verification.services import verification_service

    profile = verification_service.resolve_supplier(identifier)
    stored = profile.plan_tier.value if profile.plan_tier else "-"
    effective = _effective(profile)

    click.echo("")
    click.echo(f"  business       : {profile.business_name or '(no name)'}")
    click.echo(f"  supplier id    : {profile.supplier_id}")
    click.echo(f"  plan on record : {stored}")
    click.echo(f"  plan in effect : {effective}")
    click.echo(f"  expires        : {profile.plan_expires_at or 'never'}")
    click.echo(f"  cards per rail : {tier_rules.absolute_cap(effective)}")
    click.echo("")

    if stored != effective:
        click.echo("  THE PLAN ON RECORD HAS LAPSED. tier_rules reads an expired plan")
        click.echo("  as FREE, so this supplier's reach is already back to FREE --")
        click.echo("  no job has to run for that to be true.")
        click.echo("")

    verification = (
        profile.verification_status.value if profile.verification_status else "-"
    )
    if verification != "verified":
        click.echo("  NOTE: this supplier is not verified, so buyers cannot see them")
        click.echo("  at all. A plan changes reach, never visibility -- the curtain")
        click.echo("  is `flask verification approve`.")
        click.echo("")


@plans_cli.command("list")
@click.option("--tier", default=None, help="Only this tier.")
@click.option("--limit", default=50, show_default=True, help="How many to show.")
def list_plans(tier: str, limit: int) -> None:
    """Suppliers who are on something other than FREE, or one named tier."""
    from src.domains.supplier.supplier_profile.models.supplier_profile import (
        SupplierPlanTier,
        SupplierProfile,
    )
    from src.extensions import db

    query = db.session.query(SupplierProfile).filter(SupplierProfile.is_deleted.is_(False))
    if tier:
        query = query.filter(SupplierProfile.plan_tier == tier.strip().upper())
    else:
        # PAYING SUPPLIERS ONLY BY DEFAULT. Listing every FREE account
        # would bury the handful of rows this command exists to show.
        query = query.filter(SupplierProfile.plan_tier != SupplierPlanTier.FREE)

    rows = query.order_by(SupplierProfile.business_name.asc()).limit(limit).all()

    click.echo("")
    if not rows:
        click.echo("  Nobody is on a paid plan.\n")
        return

    click.echo(f"  ON A PLAN ({len(rows)})\n")
    for profile in rows:
        stored = profile.plan_tier.value if profile.plan_tier else "-"
        effective = _effective(profile)
        lapsed = " (LAPSED -> FREE)" if stored != effective else ""
        expires = profile.plan_expires_at.date() if profile.plan_expires_at else "never"
        click.echo(
            f"    {stored:10}{lapsed:18} {profile.business_name or '(no name)':32} "
            f"expires {expires}"
        )
    click.echo("")


@plans_cli.command("set")
@click.argument("identifier")
@click.argument("tier")
@click.option("--reason", "-r", default=None, help="Why, for the record.")
@click.option(
    "--expires",
    default=None,
    help="YYYY-MM-DD. Leave off for an open-ended plan.",
)
def set_plan(identifier: str, tier: str, reason: str, expires: str) -> None:
    """Put a supplier on a plan. TIER is FREE, PRO, MAX or PARTNER."""
    from src.cli._shared.authorise import require_capability
    from src.domains.supplier.supplier_profile.services import plan_service
    from src.domains.verification.services import verification_service

    wanted = tier.strip().upper()
    if wanted not in _tier_names():
        raise click.BadParameter(f"TIER must be one of: {', '.join(_tier_names())}")

    expires_at = None
    if expires:
        try:
            # END OF THE NAMED DAY, not the start of it. "--expires
            # 2026-12-31" from a person means the deal covers the 31st;
            # midnight would end it the moment the 30th closes, and the
            # supplier would lose a day's reach they were sold.
            day = datetime.strptime(expires, "%Y-%m-%d")
            expires_at = day.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        except ValueError:
            raise click.BadParameter("--expires must look like 2026-12-31")

    profile = verification_service.resolve_supplier(identifier)
    current = profile.plan_tier.value if profile.plan_tier else "-"

    click.echo("")
    click.echo(f"  {profile.business_name or '(no name)'}  ({profile.supplier_id})")
    click.echo(f"  {current}  ->  {wanted}")
    click.echo(f"  expires: {expires_at or 'never'}")
    click.echo("")
    click.echo("  A plan buys REACH -- more cards on a rail, a tie broken their way,")
    click.echo("  and for MAX and PARTNER the one sponsored slot in For You. It does")
    click.echo("  not buy a place in what a shop has earned, and it never decides")
    click.echo("  which offer wins for a product they already want.")

    if wanted in ("MAX", "PARTNER") and expires_at is None:
        # ASKED ABOUT SPECIFICALLY, because the tiers most likely to be
        # negotiated are the ones where an open-ended grant is most
        # likely to be an oversight -- and the cost of the oversight is
        # reach nobody is paying for, taken from the supplier who is.
        click.echo("")
        click.echo("  NO EXPIRY SET. PARTNER agreements and trials are normally")
        click.echo("  time-boxed; an open-ended one keeps its reach until somebody")
        click.echo("  remembers to come back here.")

    click.confirm(f"\n  Put this supplier on {wanted}?", abort=True)

    if not reason:
        reason = click.prompt("  Why")

    user_id, email = require_capability(SUPPLIER_PLAN)
    plan_service.set_plan(
        profile.supplier_id,
        tier=wanted,
        decided_by_user_id=user_id,
        reason=reason,
        expires_at=expires_at,
    )
    click.echo(f"\n  {profile.business_name} is on {wanted}. Recorded against {email}.\n")
