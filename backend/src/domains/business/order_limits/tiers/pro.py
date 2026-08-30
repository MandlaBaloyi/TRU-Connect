"""
Pro (subscribed) tier's own stock_order spending limits -- higher
across the board than Free. A business paying for the platform has
already demonstrated real commitment, so the same fraud/reliability
concern the Free tier's own limits guard against is genuinely lower
here -- these numbers reflect that, not an arbitrary increase.
"""
from src.domains.business.order_limits.tiers import StockOrderTierLimits

LIMITS = StockOrderTierLimits(
    monthly_manual_payment_cap_cents=1_000_000,               # R10,000/month
    cash_transaction_cap_cents=250_000,                         # R2,500/transaction
    proof_of_payment_transaction_cap_cents=300_000,              # R3,000/transaction
)
