"""
ManualPaymentProvider -- handles the DIRECT rail (and the historical
CASH / PROOF_OF_PAYMENT values it replaced). REAL, not a
stub -- this is what actually runs today. Makes ZERO external network
calls, ZERO reads of any third-party credential or config -- which is
the whole point: cash and proof-of-payment checkout must work exactly
the same whether PayFast is fully configured, half-configured, or
never touched at all. See composition.py's own docstring for how this
independence is actually enforced, not just true by convention.
"""
from __future__ import annotations

from src.domains.network.orders.models.stock_order import StockOrderPaymentMethod, StockOrderStatus
from src.domains.network.orders.providers.provider import CheckoutOutcome, PaymentProvider


class ManualPaymentProvider(PaymentProvider):
    def process_checkout(self, stock_order, payment_method: StockOrderPaymentMethod) -> CheckoutOutcome:
        # PENDING_SUPPLIER_APPROVAL FOR EVERY DIRECT METHOD, and that is
        # the rule rather than an implementation detail: the supplier is
        # releasing stock against an unsecured promise, so the order is
        # a REQUEST and their accept/decline is real. A digital payment
        # has already moved the money, so it is a PURCHASE and skips
        # this entirely (V2_00 section 2.4).
        if payment_method == StockOrderPaymentMethod.DIRECT:
            return CheckoutOutcome(
                order_status=StockOrderStatus.PENDING_SUPPLIER_APPROVAL,
                instructions=(
                    "Pay the supplier directly — cash on delivery or collection, or by transfer. "
                    "They will confirm your order shortly."
                ),
            )

        if payment_method == StockOrderPaymentMethod.CASH:
            return CheckoutOutcome(
                order_status=StockOrderStatus.PENDING_SUPPLIER_APPROVAL,
                instructions=(
                    "Pay in cash on delivery or collection. The supplier will confirm your order shortly."
                ),
            )

        if payment_method == StockOrderPaymentMethod.PROOF_OF_PAYMENT:
            return CheckoutOutcome(
                order_status=StockOrderStatus.PENDING_SUPPLIER_APPROVAL,
                instructions=(
                    "Make your payment directly to the supplier, then send them your proof of payment. "
                    "Sending proof through TruConnect directly is coming soon -- for now, send it to the "
                    "supplier's own WhatsApp number."
                ),
            )

        # Genuinely unreachable in correct use -- composition.py only
        # ever routes CASH/PROOF_OF_PAYMENT here, never PAYFAST. Raised
        # rather than silently handled, so a real routing bug in
        # composition.py surfaces immediately and loudly instead of
        # this provider quietly doing the wrong thing for a payment
        # method it was never meant to handle.
        raise ValueError(f"ManualPaymentProvider cannot handle payment_method={payment_method!r}")
