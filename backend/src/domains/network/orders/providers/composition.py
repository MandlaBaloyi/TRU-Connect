"""
get_payment_provider() -- the ONE place in this codebase that decides
which provider handles a given payment method. Every caller that needs
to process a checkout calls this function, never
`ManualPaymentProvider()` or `PayFastPaymentProvider()` directly.

THE REAL "no bad key configuration can destroy the flow" GUARANTEE
lives here, not just in manual_provider.py's own docstring: this
function ONLY ever constructs PayFastPaymentProvider when
payment_method is genuinely PAYFAST. A business paying on the DIRECT
rail never causes PayFast's config to be read, validated, or even
imported -- so a missing, empty, or malformed PayFast credential in the
environment has ZERO effect on direct checkout, today or after PayFast
is eventually wired in.
"""
from __future__ import annotations

from src.domains.network.orders.errors import PaymentProviderNotConfiguredError
from src.domains.network.orders.models.stock_order import (
    StockOrderPaymentMethod,
    is_direct_payment,
)
from src.domains.network.orders.providers.provider import PaymentProvider

_manual_provider: PaymentProvider | None = None
_payfast_provider: PaymentProvider | None = None


def get_payment_provider(payment_method: StockOrderPaymentMethod) -> PaymentProvider:
    global _manual_provider, _payfast_provider

    # ASKED, NOT LISTED. This used to enumerate CASH and
    # PROOF_OF_PAYMENT by hand, so when DIRECT was introduced it fell
    # straight through to the raise below -- the platform's own
    # payment method could not be routed to a provider at all.
    if is_direct_payment(payment_method):
        if _manual_provider is None:
            from src.domains.network.orders.providers.manual_provider import ManualPaymentProvider

            _manual_provider = ManualPaymentProvider()
        return _manual_provider

    if payment_method == StockOrderPaymentMethod.PAYFAST:
        # NOT reachable by anything in this pass -- checkout_service
        # never offers PAYFAST as a real option yet (see that module's
        # own docstring). Kept real and correct regardless, rather
        # than left entirely unimplemented, so this composition point
        # is genuinely finished the moment payfast_provider.py itself
        # is -- no second change needed here.
        if _payfast_provider is None:
            from src.domains.network.orders.providers.payfast_provider import PayFastPaymentProvider

            _payfast_provider = PayFastPaymentProvider()
        return _payfast_provider

    # Genuinely unreachable given StockOrderPaymentMethod is a closed
    # enum -- raised rather than silently falling through to a default
    # provider, since silently defaulting to SOME provider for an
    # unrecognised payment method is exactly the kind of "bad
    # configuration quietly does something" this whole design exists
    # to prevent.
    raise PaymentProviderNotConfiguredError(f"No payment provider configured for payment_method={payment_method!r}")


def reset_payment_providers() -> None:
    """Test-only -- lets each test start from clean provider instances
    rather than ones memoized across the whole test session, same
    reasoning as shared/media's own reset_media_provider."""
    global _manual_provider, _payfast_provider
    _manual_provider = None
    _payfast_provider = None
