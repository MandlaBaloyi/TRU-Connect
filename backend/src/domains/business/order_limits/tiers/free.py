"""
Free tier's own direct-payment spending limits -- these numbers exist
to bound the downside of an unverified payment method before real
trust has been established, not to generate revenue (direct payment is
commission-free, see commission.py's own docstring).

SIZED FOR A SPAZA STOCK RUN, not for a wholesaler. A typical run is a
few hundred rand to a couple of thousand; R1,000 covers an ordinary
order, and R5,000 a month covers an ordinary month for a small shop.
A business consistently trading above this is exactly who PRO is for.
"""
from src.domains.business.order_limits.tiers import StockOrderTierLimits

LIMITS = StockOrderTierLimits(
    monthly_manual_payment_cap_cents=500_000,   # R5,000/month
    direct_transaction_cap_cents=100_000,        # R1,000/transaction
)
