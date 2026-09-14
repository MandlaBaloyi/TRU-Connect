"""
`flask demand ...` -- what the demand model tells US.

THE REPORT THAT ARGUES FOR THE ECOSYSTEM (V2_15 Book Three Part 10).
"412 shops tell us they sell airtime and not one has ever bought
airtime here" is the most persuasive sentence available in a wholesaler
conversation, and until now it was computable but unreadable -- a
function with no caller is not a feature.

READ-ONLY, SO IT DOES NOT ASK WHO YOU ARE. The same asymmetry the
catalogue commands explain: anyone who can run this already holds the
database credentials, so gating a listing adds friction without safety.
Nothing here writes.

WHAT IT WILL NOT PRINT is the point of the whole file -- see
gap_service.MIN_SHOPS_TO_REPORT. A category representing fewer shops
than the threshold is withheld, and the count of withheld categories is
printed instead, because a report that silently drops small numbers
reads as "no gaps there".
"""
from __future__ import annotations

import click
from flask.cli import AppGroup

demand_cli = AppGroup("demand", help="What shops need, in aggregate.")


@demand_cli.command("gaps")
@click.option(
    "--min-shops",
    default=None,
    type=int,
    help="Lower the privacy threshold. INTERNAL INSPECTION ONLY -- output "
    "produced this way must not be shown to a supplier.",
)
def gaps(min_shops) -> None:
    """Categories shops say they buy and do not buy here."""
    from src.domains.business.demand.insights.services import gap_service

    report = gap_service.unserved_by_category(min_shops=min_shops)
    rows = report["categories"]

    click.echo("")
    click.echo("  UNSERVED DEMAND")
    click.echo(f"    shops considered : {report['shopsConsidered']:,}")
    click.echo(f"    reporting floor  : {report['minShops']} shops per category")

    if min_shops is not None and min_shops < gap_service.MIN_SHOPS_TO_REPORT:
        # LOUD, because the number on screen is no longer publishable and
        # the person reading it in a month will not remember the flag.
        click.echo("")
        click.secho(
            "    THRESHOLD LOWERED -- these numbers may identify individual "
            "shops.\n    Internal use only; do not put them in front of a supplier.",
            fg="yellow",
        )

    if not rows:
        click.echo("\n  No reportable gaps.")
        if report["suppressed"]:
            click.echo(
                f"  ({report['suppressed']} categor"
                f"{'y' if report['suppressed'] == 1 else 'ies'} below the floor, withheld)"
            )
        click.echo("")
        return

    click.echo("")
    click.echo(f"  {'CATEGORY':<28}{'WANT IT':>9}{'UNSERVED':>10}{'SHARE':>8}")
    for row in rows:
        share = f"{round(row['shareUnserved'] * 100)}%"
        click.echo(
            f"  {row['category']:<28}{row['shopsDeclaring']:>9,}"
            f"{row['shopsUnserved']:>10,}{share:>8}"
        )

    if report["suppressed"]:
        click.echo(
            f"\n  {report['suppressed']} more categor"
            f"{'y' if report['suppressed'] == 1 else 'ies'} withheld: fewer than "
            f"{report['minShops']} shops each."
        )

    click.echo("")
    click.echo("  A category at 100% is a hole in the catalogue.")
    click.echo("  A category part-served is a supplier who cannot keep up.")
    click.echo("")
