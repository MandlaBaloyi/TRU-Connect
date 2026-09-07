"""
Max tier's own direct-payment ceiling -- R50,000/month.

THE TOP OF SELF-SERVE, not the top of the platform. A supplier moving
more than R50,000 a month off-platform is past the point where a
signup form is the right way in: that is a wholesaler with their own
systems, and the answer is a sales conversation and a real
integration, not a bigger number here.

Named max_tier rather than max so it never shadows the builtin.
"""
from src.domains.supplier.order_limits.tiers import DirectPaymentTierLimits

LIMITS = DirectPaymentTierLimits(
    monthly_direct_receipts_cap_cents=5_000_000,  # R50,000/month
)
