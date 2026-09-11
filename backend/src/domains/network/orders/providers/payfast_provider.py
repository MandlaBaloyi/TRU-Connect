"""
PayFastPaymentProvider -- NOT IMPLEMENTED YET. This is the ONE file in
this entire codebase that will ever import the PayFast SDK, build a
PayFast request, or parse a PayFast response, once this is built for
real. Every other file in checkout/ -- checkout_service.py, the
routes, cart_service.py -- talks only to the abstract PaymentProvider
interface (provider.py) and has no idea PayFast exists.

REAL FINDINGS FROM RESEARCH, kept here so building this for real later
starts from confirmed facts, not marketing pages re-read from scratch:

- PayFast's Split Payments feature allocates exactly ONE secondary
  ("receiving") merchant per transaction. The PRIMARY merchant is
  whoever actually receives the customer's payment first.
- IN OUR MODEL: each SUPPLIER is the primary merchant (they're the one
  actually selling the goods) -- TruConnect would be the SECONDARY,
  only ever receiving a split-off commission, if and when TruConnect
  decides to charge one. This means EVERY SUPPLIER who wants to accept
  real digital payments needs their OWN PayFast merchant account,
  linked during their own onboarding -- not something this provider
  can create for them.
- A NEW FIELD IS NEEDED ON SupplierProfile (payfast_merchant_id, likely
  also a merchant key, mirroring the whatsapp/email/tiktok contact
  field pattern already there) BEFORE this provider can function for
  any given supplier -- checked, and if absent, PAYFAST simply isn't
  offered as a payment option for that supplier's checkout (this
  provider should raise a clear, specific error in that case, never
  silently fall back to a different payment method the business didn't
  choose).
- PayFast confirms payment via ITN (Instant Transaction Notification)
  -- a webhook call to a publicly reachable notify_url, which must be
  signature-verified before being trusted (same shape as
  shared/media's own Cloudinary webhook -- see
  shared/media/webhooks/webhook_service.py for the proven pattern to
  mirror: verify_webhook_signature on the provider interface, a
  dedicated route, a real 200-response-prevents-retries contract).
- A real sandbox environment exists for testing before going live --
  confirmed directly from PayFast's own developer documentation and
  multiple independent integration guides, not assumed.
- Split amount can be a fixed amount, a percentage, or a combination
  of both, configured per transaction.

WHAT THIS FILE WILL EVENTUALLY NEED, not built now:
- A real HTTP client call (or their SDK, if using one) building the
  split-payment request with the supplier's own Merchant ID/Key as the
  receiving party.
- process_checkout returning order_status=AWAITING_PAYMENT and a real
  redirect_url the business is sent to in order to actually pay.
- A companion itn_service.py (in shared/checkout/webhooks/) that
  verifies the ITN callback and transitions the order from
  AWAITING_PAYMENT to CONFIRMED once payment is genuinely confirmed --
  never on the redirect alone, only on a verified server-to-server
  notification, exactly like Cloudinary's own webhook is the only
  trusted source for a scan result, never the client's own claim.
"""
from __future__ import annotations

from src.domains.network.orders.providers.provider import CheckoutOutcome, PaymentProvider


class PayFastPaymentProvider(PaymentProvider):
    def process_checkout(self, stock_order, payment_method) -> CheckoutOutcome:
        raise NotImplementedError(
            "PayFast integration isn't wired yet. See this file's own module docstring for what's already "
            "confirmed and what's still needed before this can be implemented for real."
        )
