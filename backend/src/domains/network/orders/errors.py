"""
domains.network.orders exceptions -- all real src.core.exceptions.AppError
subclasses, same convention as every other domain in this codebase.
"""
from __future__ import annotations

from src.core.exceptions import AppError, ConflictError, NotFoundError, ValidationError


class SupplierNotFoundError(NotFoundError):
    code = "SUPPLIER_NOT_FOUND"


class SupplierNotConnectedError(ConflictError):
    """THE REAL, CONFIRMED CONSTRAINT this domain never actually
    enforced -- found and fixed after direct report, reproduced
    exactly from a real log: disconnect from a supplier, send a new
    (still-pending) connection request, then submit_checkout still
    succeeded. Browsing a supplier's catalogue and building a cart
    are both genuinely allowed without an active connection -- that
    part was correct and stays unchanged (cart_service.py has no
    connection check, on purpose). Only the real financial commitment
    -- actually submitting an order -- requires the connection to be
    genuinely ACTIVE. A pending, declined, or ended connection all
    raise this same error, deliberately indistinguishable, matching
    the same "don't reveal the exact state of a relationship to the
    other side" reasoning already established for
    ConnectionNotActiveError in the connections domain itself (this
    error is NOT that one, reused -- deliberately a new, orders-owned
    class, since importing another domain's own error class directly
    would create the same kind of cross-domain coupling this
    codebase's error-per-domain discipline avoids everywhere else)."""

    code = "SUPPLIER_NOT_CONNECTED"


class ProductNotFoundError(NotFoundError):
    """Raised for a genuinely nonexistent product, one belonging to a
    DIFFERENT supplier than the cart itself is for, or an archived
    one -- all three deliberately indistinguishable from the caller's
    perspective, same IDOR-safety reasoning already established
    throughout this codebase (see connections' own
    SUPPLIER_NOT_FOUND/PRODUCT_NOT_FOUND precedent)."""

    code = "PRODUCT_NOT_FOUND"


class OutOfStockError(ConflictError):
    """Raised when trying to add a product with zero available stock
    to a cart -- a REAL BUG FOUND after direct report: this check
    never existed at all, so an out-of-stock product could be added
    the same as an in-stock one. Deliberately its OWN error, never
    folded into ProductNotFoundError -- "out of stock" and "doesn't
    exist" are genuinely different facts, and the frontend needs to
    tell them apart to show the right message ("out of stock right
    now" versus "this product isn't available at all"). Carries the
    real product_id so the frontend can name the exact item, not just
    show a generic rejection."""

    code = "OUT_OF_STOCK"


class CartNotFoundError(NotFoundError):
    """Raised when an operation needs an EXISTING cart (update/remove
    an item, view a specific cart by id) and none exists -- distinct
    from add_item, which is allowed to create one via
    get_or_create_cart; this error is for the "you can't update or
    check out something that was never started" case."""

    code = "CART_NOT_FOUND"


class OrderNotFoundError(NotFoundError):
    """Raised for a genuinely nonexistent order, or one that exists
    but belongs to a different business or a different supplier than
    the one asked for -- deliberately indistinguishable from the
    caller's perspective, same IDOR-safety reasoning as
    StockOrderRepository.get_by_id_for_business_and_supplier's own
    docstring."""

    code = "ORDER_NOT_FOUND"


class CartItemNotFoundError(NotFoundError):
    code = "CART_ITEM_NOT_FOUND"


class InvalidQuantityError(ValidationError):
    """Raised for a quantity of zero or less -- update_item_quantity
    never removes an item as a side effect of "quantity 0"; removal is
    always an explicit, separate action (remove_item), so this stays a
    real, surfaced validation error rather than silent, ambiguous
    behaviour."""

    code = "INVALID_QUANTITY"


class EmptyCartError(ConflictError):
    """Raised when checkout is attempted on a cart with zero items --
    a real, meaningful state that should never reach the payment
    layer."""

    code = "EMPTY_CART"


class DeliveryNotOfferedError(ValidationError):
    """Raised when a DELIVER order is submitted to a supplier who has
    said they don't deliver (SupplierProfile.offers_delivery is False).

    A real, separate error from the generic validation ones: the
    business didn't get anything WRONG, the supplier simply doesn't
    offer that option, so the message names the supplier rather than
    blaming the input. Enforced here and not only in the UI -- the
    frontend already defaults these carts to COLLECT and hides the
    address pickers, but a client is never the gate."""

    code = "DELIVERY_NOT_OFFERED"


class BelowMinimumOrderError(ConflictError):
    """Raised when a cart total is under the supplier's own
    minimum_order_cents.

    ConflictError, not ValidationError -- nothing about the request is
    malformed; the cart is simply in a state that can't be submitted
    yet, exactly like EmptyCartError above. Carries the shortfall in
    `data` so the frontend can say "add R120 more" rather than making
    the business do the arithmetic."""

    code = "BELOW_MINIMUM_ORDER"


class PaymentMethodNotAvailableError(ValidationError):
    """Raised for a payment method that exists on the enum (see
    StockOrderPaymentMethod's own docstring on why PAYFAST is modelled
    now regardless) but isn't genuinely offered by checkout_service
    yet -- a deliberately distinct error from EmptyCartError, which
    means something entirely different (nothing to check out at all).
    Misusing one error for two unrelated meanings is exactly the kind
    of ambiguity this codebase's own error-naming discipline exists to
    prevent."""

    code = "PAYMENT_METHOD_NOT_AVAILABLE"


class OrderLimitExceededError(ConflictError):
    """Raised when a CASH or PROOF_OF_PAYMENT order exceeds
    constants.checkout_limits.MANUAL_PAYMENT_ORDER_LIMIT_CENTS -- see
    that constant's own docstring for the full reasoning (neither
    method is verified before the supplier commits to fulfilling, so
    both get the SAME cap; PAYFAST is never subject to this, since a
    real gateway confirms payment before the order proceeds).

    Carries `data` naming the real order total and the real limit, so
    the frontend can show a genuinely specific message ("R6,000 is
    over the R5,000 limit for this payment method") rather than a
    generic rejection."""

    code = "ORDER_LIMIT_EXCEEDED"


class CartAlreadySubmittedError(ConflictError):
    """Raised when an operation that requires status=CART (add/update/
    remove/checkout) is attempted on a StockOrder that's already
    SUBMITTED -- a submitted order is a real, historical record now,
    never silently mutable again."""

    code = "CART_ALREADY_SUBMITTED"


class OrderNotCancellableError(ConflictError):
    """Raised when a business tries to cancel an order that isn't (or
    is no longer) PENDING_SUPPLIER_APPROVAL -- once a supplier has
    decided either way, this is the wrong door: DECLINED/CANCELLED
    are already terminal, and CONFIRMED specifically routes the
    business to contact their supplier directly instead (see
    cancellation_service.py's own module docstring for the full
    architecture and why that's a deliberate choice, not a gap)."""

    code = "ORDER_NOT_CANCELLABLE"


class DigitalPaymentCancellationNotSupportedError(AppError):
    """Genuinely unreachable today -- PAYFAST orders can't exist yet
    (see StockOrderPaymentMethod's own comment). Exists as a real,
    deliberate guard rather than silent trust that this code path
    will never see one: a digital payment needs its own refund-
    integrated cancellation flow through the real payment gateway,
    not this manual, reason-and-notify one built for CASH/PROOF_OF_PAYMENT.
    Whoever eventually builds real PAYFAST cancellation should see
    this error and know exactly why it's here, not silently inherit
    a cash-shaped flow that was never designed for it."""

    status_code = 409
    code = "DIGITAL_PAYMENT_CANCELLATION_NOT_SUPPORTED"


class StaleCartItemError(ConflictError):
    """Raised at checkout time when a cart contains an item whose
    product has since been archived or deleted -- never silently
    dropped or silently let through with a price that might no longer
    reflect what the supplier actually intends to sell it for. Carries
    `data` naming exactly which item(s) are stale so the frontend can
    show a real, specific message rather than a generic failure."""

    code = "STALE_CART_ITEM"


class PaymentProviderNotConfiguredError(AppError):
    """A real, deliberate distinct error -- see providers/
    composition.py's own docstring on why a missing or misconfigured
    payment provider must NEVER silently degrade into some other
    payment method or silently fail a checkout in a confusing way. It
    surfaces clearly, as this specific, named condition."""

    status_code = 503
    code = "PAYMENT_PROVIDER_NOT_CONFIGURED"
