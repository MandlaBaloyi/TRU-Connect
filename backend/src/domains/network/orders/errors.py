"""
domains.network.orders exceptions -- all real src.core.exceptions.AppError
subclasses, same convention as every other domain in this codebase.
"""
from __future__ import annotations

from src.core.exceptions import AppError, ConflictError, NotFoundError, ValidationError


class SupplierNotFoundError(NotFoundError):
    code = "SUPPLIER_NOT_FOUND"


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
