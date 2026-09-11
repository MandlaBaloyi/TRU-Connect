"""
Free tier's own direct-payment ceiling.

R10,000/month is deliberately TIGHT, and the tightness is the
strategy rather than an oversight. Set against the FREE business cap
of R5,000/month, this carries roughly two buyers at full tilt -- so a
supplier building any real book meets it quickly.

That is intended. TruConnect's self-serve tiers are sized for the
small suppliers the platform targets first; a supplier consistently
moving more than this is either ready to pay for PRO, or big enough
that they belong in a sales conversation with a real integration
behind it, not a signup form.
"""
from src.domains.supplier.order_limits.tiers import DirectPaymentTierLimits

LIMITS = DirectPaymentTierLimits(
    monthly_direct_receipts_cap_cents=1_000_000,  # R10,000/month
)
