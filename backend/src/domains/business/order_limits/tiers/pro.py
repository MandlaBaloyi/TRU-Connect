"""
Pro (subscribed) tier's own direct-payment spending limits -- double
Free across the board. A business paying for the platform has already
demonstrated real commitment, so the same fraud/reliability concern
the Free tier's limits guard against is genuinely lower here; these
numbers reflect that, not an arbitrary increase.
"""
from src.domains.business.order_limits.tiers import StockOrderTierLimits

LIMITS = StockOrderTierLimits(
    monthly_manual_payment_cap_cents=1_000_000,  # R10,000/month
    direct_transaction_cap_cents=200_000,         # R2,000/transaction
)
