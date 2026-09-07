"""
The SUPPLIER side of the direct-payment caps -- "how much money may
this supplier receive off-platform in a month", tier-gated, living
next to the code that enforces it.

WHY A SUPPLIER-SIDE CAP EXISTS AT ALL, given there was already a
business-side one. The buyer cap bounds what one BUSINESS can move
invisibly. It does nothing about the other end: a supplier serving ten
buyers, each comfortably inside their own R5,000, receives R50,000 a
month that TRU Connect never sees. The exposure the caps exist to
bound is the TOTAL of invisible money crossing the platform, and half
of it was unbounded.

It also closes a commercial hole. Direct payment carries no
commission (commission.py), so without a ceiling the rational choice
for every supplier is direct-only forever -- no revenue, and worse, no
visible trading record. Which brings us to the real reason:

THIS IS NOT PRIMARILY A REVENUE CONTROL. The platform constitution's
own framing (00A, lines 258-262) is that informal trade "remains
invisible to the formal financial system", and that "without
measurable trust, access to finance remains limited". Every direct
order is invisible activity; every digital one is a verifiable
trading record. These caps are the mechanism that grows the evidence
base the lending stage depends on -- infrastructure before finance,
exactly as that document requires.

NO PER-TRANSACTION CAP ON THIS SIDE, deliberately. A supplier does not
choose the size of an order -- the buyer does, and the buyer's own
per-transaction cap already bounds it. A second ceiling on the same
number would block the same thing twice, and whoever hit it would have
no way to tell which of the two stopped them.

USES THE SUPPLIER'S OWN Tier (FREE/PRO/MAX), never BusinessTier -- see
domains/supplier/tiers/tier.py on why the two roles' subscriptions are
deliberately separate types rather than one shared enum.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.domains.supplier.tiers.tier import Tier


@dataclass(frozen=True)
class DirectPaymentTierLimits:
    """A rolling calendar-month ceiling on direct (off-platform)
    receipts, plus where to warn on the way up."""

    monthly_direct_receipts_cap_cents: int

    # WARN BEFORE BLOCKING, always. A supplier who discovers the cap by
    # being stopped mid-trade has been ambushed by a rule they were
    # never shown; one who saw it coming at 75% can pace themselves,
    # upgrade, or move buyers to digital. Fractions rather than
    # absolute amounts so they stay correct when the cap changes.
    warn_at_fractions: tuple[float, ...] = (0.75, 0.90)

    # WHETHER THE CAP ACTUALLY BLOCKS, or only warns.
    #
    # OFF FOR NOW, AND THAT IS DELIBERATE RATHER THAN UNFINISHED. The
    # cap's whole purpose is to move suppliers onto the digital rail --
    # but the gateway is not wired yet, so today there is no rail to
    # move to. Blocking now would not redirect a supplier, it would
    # simply stop them trading, and they would be right to blame TRU
    # Connect for it.
    #
    # Warnings run from day one regardless: they cost a supplier
    # nothing, and they mean the limit is already familiar by the time
    # it bites. Flip this to True the day digital payments genuinely
    # work -- it is a number in a file, not a code change.
    blocks_when_exceeded: bool = False


def get_direct_payment_limits(tier: Tier) -> DirectPaymentTierLimits:
    from src.domains.supplier.order_limits.tiers import free, max_tier, pro

    limits = {
        Tier.FREE: free.LIMITS,
        Tier.PRO: pro.LIMITS,
        Tier.MAX: max_tier.LIMITS,
    }
    if tier not in limits:
        raise ValueError(f"No direct-payment limits defined for supplier tier={tier!r} yet.")
    return limits[tier]
