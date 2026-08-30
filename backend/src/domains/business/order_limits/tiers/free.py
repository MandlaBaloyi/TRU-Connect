"""
Free tier's own stock_order spending limits -- these numbers exist to
bound the downside of a manual (unverified) payment method before real
trust has been established, not to generate revenue (manual methods
are commission-free, see commission.py's own docstring).
"""
from src.domains.business.order_limits.tiers import StockOrderTierLimits

LIMITS = StockOrderTierLimits(
    monthly_manual_payment_cap_cents=500_000,               # R5,000/month
    cash_transaction_cap_cents=100_000,                      # R1,000/transaction
    proof_of_payment_transaction_cap_cents=200_000,           # R2,000/transaction
)
