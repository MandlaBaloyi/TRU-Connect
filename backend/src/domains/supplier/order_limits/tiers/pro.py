"""
Pro tier's own direct-payment ceiling -- R25,000/month.

Two and a half times Free. A supplier paying for the platform has
demonstrated real commitment, which lowers the same concern the Free
ceiling guards against; this reflects that rather than being an
arbitrary bump.
"""
from src.domains.supplier.order_limits.tiers import DirectPaymentTierLimits

LIMITS = DirectPaymentTierLimits(
    monthly_direct_receipts_cap_cents=2_500_000,  # R25,000/month
)
