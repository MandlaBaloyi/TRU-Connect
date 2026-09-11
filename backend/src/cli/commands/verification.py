"""
`flask verification ...` -- opening and closing the curtain.

THE MANUAL SWITCH, AND WHY IT IS ENOUGH FOR NOW. V2_12 Phase 1 builds
the curtain before the document pipeline, deliberately: the curtain is
what makes the platform safe, and it holds no personal data at all. A
decision here is made by a human who looked at something out-of-band --
a certificate photographed and sent over WhatsApp, a phone call, a
supplier they have met -- and records the outcome with a reason.

Phase 2 replaces "looked at something out-of-band" with an intake
pipeline and an audited review queue. These commands keep working
unchanged; they will simply have more to read before deciding.

SAME SHAPE AS `flask catalogue ...` on purpose. `status` and `pending`
read, `approve` and `revoke` write, the writes ask who you are, and
the capability asked for is supplier:verify. A reviewer working two
queues with one vocabulary makes fewer mistakes than one learning two.
"""
from __future__ import annotations

import click
from flask.cli import AppGroup

from src.cli._shared.capabilities import SUPPLIER_VERIFY

verification_cli = AppGroup("verification", help="Approve or revoke supplier verification.")


def _line(profile) -> str:
    status = profile.verification_status.value if profile.verification_status else "-"
    mark = "LIVE   " if status == "verified" else "hidden "
    return f"    {mark} {profile.business_name or '(no name)':32} {status:12} {profile.supplier_id}"


@verification_cli.command("pending")
@click.option("--limit", default=50, show_default=True, help="How many to show.")
def pending(limit: int) -> None:
    """Suppliers nobody can see yet, newest first."""
    from src.domains.supplier.supplier_profile.models.supplier_profile import (
        SupplierVerificationStatus,
    )
    from src.domains.verification.services import verification_service

    waiting = verification_service.list_by_status(SupplierVerificationStatus.UNVERIFIED, limit=limit)
    click.echo("")
    if not waiting:
        click.echo("  Nobody is waiting. Every supplier with a profile is visible.\n")
        return

    click.echo(f"  WAITING ({len(waiting)})\n")
    for profile in waiting:
        click.echo(_line(profile))
    click.echo("")
    click.echo("  flask verification status <email|id>              one supplier")
    click.echo("  flask verification approve <email|id> -r '...'    open the curtain")
    click.echo("")


@verification_cli.command("status")
@click.argument("identifier")
def status(identifier: str) -> None:
    """One supplier, by email or user id."""
    from src.domains.verification.services import verification_service
    from src.domains.verification.visibility import is_visible_to_buyers

    profile = verification_service.resolve_supplier(identifier)
    visible = is_visible_to_buyers(profile)
    click.echo("")
    click.echo(f"  business       : {profile.business_name or '(no name)'}")
    click.echo(f"  supplier id    : {profile.supplier_id}")
    click.echo(f"  status         : {profile.verification_status.value if profile.verification_status else '-'}")
    click.echo(f"  buyers see them: {'YES' if visible else 'NO'}")
    if not visible:
        click.echo("")
        click.echo("  They can still build everything -- catalogue, prices, settings.")
        click.echo("  They simply do not appear in search and cannot be ordered from.")
    click.echo("")


@verification_cli.command("approve")
@click.argument("identifier")
@click.option("--reason", "-r", default=None, help="What you checked, and how.")
def approve(identifier: str, reason: str) -> None:
    """Open the curtain: this supplier becomes findable and sellable."""
    from src.cli._shared.authorise import require_capability
    from src.domains.verification.services import verification_service

    profile = verification_service.resolve_supplier(identifier)
    click.echo("")
    click.echo(f"  {profile.business_name or '(no name)'}  ({profile.supplier_id})")
    click.echo("")
    click.echo("  Approving means businesses can find this supplier, browse their")
    click.echo("  catalogue, and send them money. Be sure you checked something real.")
    click.confirm("\n  Make this supplier visible to buyers?", abort=True)

    # ASKED IF NOT SUPPLIED, never defaulted. A blank reason produces a
    # record saying a supplier was verified by somebody for reasons
    # nobody wrote down -- which is worthless in three months, and
    # three months is exactly when it gets asked about.
    if not reason:
        reason = click.prompt("  What did you check")

    user_id, email = require_capability(SUPPLIER_VERIFY)
    verification_service.approve(profile.supplier_id, decided_by_user_id=user_id, reason=reason)
    click.echo(f"\n  {profile.business_name} is now visible to buyers. Recorded against {email}.\n")


@verification_cli.command("revoke")
@click.argument("identifier")
@click.option("--reason", "-r", default=None, help="Why, for the record.")
def revoke(identifier: str, reason: str) -> None:
    """Close the curtain again. Their work is untouched; only visibility changes."""
    from src.cli._shared.authorise import require_capability
    from src.domains.verification.services import verification_service

    profile = verification_service.resolve_supplier(identifier)
    click.echo("")
    click.echo(f"  {profile.business_name or '(no name)'}  ({profile.supplier_id})")
    click.echo("")
    click.echo("  Their catalogue, prices, connections and past orders all survive.")
    click.echo("  They stop appearing in search and cannot be ordered from again.")
    click.confirm("\n  Hide this supplier from buyers?", abort=True)

    if not reason:
        reason = click.prompt("  Why")

    user_id, email = require_capability(SUPPLIER_VERIFY)
    verification_service.revoke(profile.supplier_id, decided_by_user_id=user_id, reason=reason)
    click.echo(f"\n  {profile.business_name} is hidden from buyers. Recorded against {email}.\n")
