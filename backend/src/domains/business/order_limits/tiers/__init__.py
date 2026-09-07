"""
stock_order's own per-tier spending limits -- everything about "how
much can this business move through a manual (unverified) payment
method", tier-gated, living right next to the code that enforces it.
Mirrors domains/supplier/products/tiers/__init__.py's own shape
exactly -- same discipline, different domain.

Deliberately NOT in shared/checkout -- see that package's own module
docstring on why: shared/checkout is the neutral infrastructure both
business and supplier depend on (the data model, the payment provider
abstraction), and has no business owning it, so it must never contain
a business RULE like "how much can a FREE-tier business spend this
month". That's a decision domains/business/stock_order owns, the same
way domains/supplier/products owns what a tier means for uploads.

USES BusinessTier, NOT the supplier's own Tier -- these are
deliberately separate, independent concepts (see
domains/business/tiers/tier.py's own docstring for the full
reasoning): a business's spending-limit subscription and a supplier's
upload-limit subscription are genuinely different products, never
mixed at the type level.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.domains.business.tiers.tier import BusinessTier


@dataclass(frozen=True)
class StockOrderTierLimits:
    # A single, rolling calendar-month ceiling across BOTH manual
    # methods combined (cash + proof-of-payment together) -- this is
    # the real fix for the exact loophole caught during review: a
    # business splitting one large order into several smaller ones
    # over several days must still be bounded by ONE real number, not
    # reset by simply switching which manual method they use.
    monthly_manual_payment_cap_cents: int

    # ONE per-transaction ceiling, across the whole direct rail.
    #
    # THERE USED TO BE TWO -- a lower one for cash and a higher one for
    # proof-of-payment, on the reasoning that a traceable transfer is
    # safer than notes. TRU Connect could never enforce that
    # difference: nothing stopped a buyer selecting proof-of-payment
    # for the higher cap and then handing over cash. The two methods
    # were merged into DIRECT (see StockOrderPaymentMethod), so the two
    # caps merged with them.
    #
    # IT ALSO BOUNDS CANCELLATION DAMAGE, not just invisible money.
    # Checkout RESERVES inventory at submission
    # (InventoryRepository.reserve_quantity), so a large order that is
    # later cancelled has been sitting on a small supplier's stock the
    # whole time it was pending. Capping the single order caps how much
    # of a supplier's shelf one buyer can freeze.
    direct_transaction_cap_cents: int


def get_stock_order_limits(tier: BusinessTier) -> StockOrderTierLimits:
    from src.domains.business.order_limits.tiers import free, pro

    limits = {
        BusinessTier.FREE: free.LIMITS,
        BusinessTier.PRO: pro.LIMITS,
    }
    if tier not in limits:
        raise ValueError(f"No stock_order spending limits defined for tier={tier!r} yet.")
    return limits[tier]
