"""
PaymentProvider -- the abstract contract every payment method
implements. This is what makes "PayFast can be wired in later without
rewriting checkout_service.py" true rather than a claim:
checkout_service.py depends on THIS interface, never on
manual_provider.py, payfast_provider.py, or the PayFast SDK/HTTP calls
directly. Adding PayFast for real means writing one class in
payfast_provider.py and changing one function's body (composition.py's
own get_payment_provider) -- no other file in this codebase needs to
change.

Same isolation shape as shared/media/providers/provider.py, deliberately
mirrored rather than invented fresh -- that pattern is already proven
in this codebase (Cloudinary swappable behind MediaProvider), and this
is the exact same kind of problem: one abstraction, one real
implementation today, one external-service implementation to come
later.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.domains.network.orders.models.stock_order import StockOrder, StockOrderPaymentMethod, StockOrderStatus


@dataclass(frozen=True)
class CheckoutOutcome:
    """The result of a provider handling a submission -- provider-
    agnostic on purpose, same reasoning as shared/media's own
    SignedUpload/ScanResult dataclasses.

    order_status is what checkout_service should actually WRITE onto
    the StockOrder -- CASH/PROOF_OF_PAYMENT go straight to SUBMITTED
    (no external step to wait for); a real gateway would return
    AWAITING_PAYMENT instead, since the order isn't genuinely
    submitted until a redirect-and-return payment actually succeeds.

    redirect_url is None for every provider in this pass -- it exists
    now so a future real gateway's own "send the business here to pay"
    step doesn't require changing this dataclass's own shape, only
    populating a field that's already there.

    instructions is the ONE thing CASH and PROOF_OF_PAYMENT actually
    need to give back -- real, user-facing text ("Pay the driver on
    delivery", "Send your proof of payment to..."), not a placeholder.
    """

    order_status: "StockOrderStatus"
    redirect_url: Optional[str] = None
    instructions: Optional[str] = None


class PaymentProvider(ABC):
    @abstractmethod
    def process_checkout(
        self, stock_order: "StockOrder", payment_method: "StockOrderPaymentMethod"
    ) -> CheckoutOutcome:
        """Given a cart that's about to be submitted and the payment
        method the business chose, does whatever THIS provider needs
        to do (nothing at all, for manual methods; a real gateway call,
        for a future digital-payment provider) and returns the
        outcome. The caller (checkout_service) has already validated
        the cart itself (non-empty, every item still genuinely
        orderable) BEFORE calling this -- a provider's own job is only
        ever "handle the payment side of an already-valid cart", never
        cart validation."""
