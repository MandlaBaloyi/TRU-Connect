"""
Platform commission calculation -- a pure function, deliberately
separate from checkout_service.py's own orchestration logic, so this
one real piece of money-math can be tested directly and exhaustively
without needing a database, a request, or any other moving part.

Lives in domains/business/stock_order, not shared/checkout -- "how
much does TRU Connect charge on this order" is a real business
revenue rule, owned the same way the tier spending limits are (see
tiers/__init__.py's own docstring for the identical reasoning).

The two band constants are inlined here rather than pulled from a
separate constants file -- small enough, and specific enough to this
one calculation, that a dedicated file would be more indirection than
the two numbers are worth.
"""
from __future__ import annotations

from src.domains.network.orders.models.stock_order import StockOrderPaymentMethod

# CASH and PROOF_OF_PAYMENT are commission-free, always -- no
# technical means to collect a cut on money that never touches a
# digital system. Only PAYFAST ever produces a non-zero result.
#
# A stepped, fixed fee per band -- NOT a percentage. R5 for every
# complete R500 the order totals (floor division), so an order under
# R500 pays nothing at all -- this falls out of the formula itself,
# not as a separate special case. "We have the right to change this
# policy at any time" -- these two numbers are the whole policy;
# changing either is the entire change needed.
COMMISSION_BAND_SIZE_CENTS = 50_000  # R500 per band
COMMISSION_FEE_PER_BAND_CENTS = 500  # R5 charged per complete band


def calculate_platform_commission_cents(order_total_cents: int, payment_method: StockOrderPaymentMethod) -> int:
    """Confirmed directly against the exact examples given when this
    policy was defined: R499 -> R0, R500 -> R5, R999 -> R5 (still one
    band), R1000 -> R10 (the second band starts)."""
    if payment_method != StockOrderPaymentMethod.PAYFAST:
        return 0

    bands = order_total_cents // COMMISSION_BAND_SIZE_CENTS
    return bands * COMMISSION_FEE_PER_BAND_CENTS
