"""
`flask catalogue ...` -- inspecting and working the match review queue.

READ FIRST, DECIDE SECOND. `reviews` and `review` show what the ladder
proposed and on what evidence; `accept` and `reject` act. Nothing here
writes without being asked to, so the listing commands are safe to run
against production while thinking.

ONLY THE WRITES ASK WHO YOU ARE, and the asymmetry is deliberate.
Anyone able to run these already holds the database credentials and
could read the same rows with psql, so gating the listings would add
friction without adding safety. The writes are different: they change
what every supplier sees. See _shared/authorise.py -- the prompt is
a signature, not a wall, and what it asks for is a CAPABILITY
(catalogue:review) rather than a person.
"""
from __future__ import annotations

import click
from flask.cli import AppGroup

from src.cli._shared.capabilities import CATALOGUE_REVIEW
from src.cli._shared.formatting import pct, render_evidence

catalogue_cli = AppGroup("catalogue", help="Inspect and work the product catalogue.")


@catalogue_cli.command("reviews")
@click.option("--limit", default=20, show_default=True, help="How many to show.")
def reviews(limit: int) -> None:
    """The pending queue, highest confidence first."""
    from src.domains.catalogue.matching.services import review_service

    counts = review_service.counts()
    click.echo("")
    click.echo("  QUEUE")
    for status, count in sorted(counts.items()):
        click.echo(f"    {status:14} {count:>6,}")
    if not counts:
        click.echo("    (nothing recorded yet)")

    pending = review_service.list_pending(limit=limit)
    if not pending:
        click.echo("\n  Nothing waiting for a decision.\n")
        return

    click.echo(f"\n  PENDING ({len(pending)} shown)\n")
    for review in pending:
        click.echo(f"  {review.id}")
        click.echo(f"    supplier wrote : {review.source_text}")
        click.echo(f"    proposed       : {_product_label(review.proposed_product_id)}")
        click.echo(f"    tier           : {review.tier}   confidence {pct(review.confidence)}")
        click.echo(f"    because        : {review.reason}")
        click.echo(render_evidence(review.evidence or {}))
        click.echo("")
    click.echo("  flask catalogue review <id>          to see one in full")
    click.echo("  flask catalogue accept <id>          to confirm it")
    click.echo("  flask catalogue reject <id> -r '...' to refuse it\n")


def _product_label(product_id) -> str:
    if product_id is None:
        return "(nothing -- the ladder found no plausible product)"
    from src.domains.catalogue.products.models.product import Product

    product = Product.query.filter_by(id=product_id).first()
    if product is None:
        return f"{product_id} (deleted)"
    bits = [product.name]
    if product.gtin:
        bits.append(f"barcode {product.gtin}")
    if product.unit_quantity and product.unit_measure:
        bits.append(f"{product.unit_quantity}{product.unit_measure.value}")
    return "  |  ".join(bits)


@catalogue_cli.command("review")
@click.argument("review_id")
def review(review_id: str) -> None:
    """One review, in full, with its evidence."""
    from src.domains.catalogue.matching.services import review_service

    item = review_service.get(review_id)
    click.echo("")
    click.echo(f"  id             : {item.id}")
    click.echo(f"  status         : {item.status.value}")
    click.echo(f"  decided by     : {item.decided_by_source}")
    click.echo(f"  supplier wrote : {item.source_text}")
    click.echo(f"  proposed       : {_product_label(item.proposed_product_id)}")
    click.echo(f"  tier           : {item.tier}   confidence {pct(item.confidence)}")
    click.echo(f"  because        : {item.reason}")
    click.echo("  evidence       :")
    click.echo(render_evidence(item.evidence or {}))
    click.echo("")


@catalogue_cli.command("accept")
@click.argument("review_id")
def accept(review_id: str) -> None:
    """Confirm a proposal: link the offer and teach the alias.

    THE ALIAS IS WHY THIS MATTERS MORE THAN ONE ROW. It is global -- the
    next supplier who writes the same words gets matched for free, so
    the queue shrinks rather than repeating itself. It is also why this
    asks who you are: an action whose blast radius is every supplier on
    the platform should carry a name.
    """
    from src.cli._shared.authorise import require_capability
    from src.domains.catalogue.matching.services import review_service

    item = review_service.get(review_id)
    click.echo(f'\n  "{item.source_text}"')
    click.echo(f"  -> {_product_label(item.proposed_product_id)}\n")
    click.confirm("  Link these, and remember it for every supplier?", abort=True)

    # AFTER the confirmation, not before. No reason to make somebody
    # type a password for an action they then decide against.
    user_id, email = require_capability(CATALOGUE_REVIEW)

    review_service.accept(review_id, decided_by_user_id=user_id)
    click.echo(f"  Linked, and the alias was learned. Recorded against {email}.\n")


@catalogue_cli.command("reject")
@click.argument("review_id")
@click.option("--reason", "-r", default=None, help="Why, for the record.")
def reject(review_id: str, reason: str) -> None:
    """Refuse a proposal. The offer stays unmatched, which is safe."""
    from src.cli._shared.authorise import require_capability
    from src.domains.catalogue.matching.services import review_service

    item = review_service.get(review_id)
    click.echo(f'\n  "{item.source_text}"')
    click.echo(f"  -> {_product_label(item.proposed_product_id)}\n")
    click.confirm("  Refuse this match?", abort=True)

    user_id, email = require_capability(CATALOGUE_REVIEW)

    review_service.reject(review_id, decided_by_user_id=user_id, reason=reason)
    click.echo(f"  Rejected by {email}. The offer stays unmatched, and no alias was written.\n")
