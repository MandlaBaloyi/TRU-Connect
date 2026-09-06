"""
domains.supplier.stock_order_management exceptions -- all real
src.core.exceptions.AppError subclasses, same convention as every
other domain in this codebase.
"""
from __future__ import annotations

from src.core.exceptions import AppError, ConflictError, NotFoundError


class OrderNotFoundError(NotFoundError):
    """Raised for a genuinely nonexistent order, or one that exists
    but belongs to a different supplier -- deliberately
    indistinguishable, same IDOR-safety reasoning as every other
    domain in this codebase (mirrors domains.network.orders' own
    OrderNotFoundError, scoped from the supplier's own side instead
    of the business's)."""

    code = "ORDER_NOT_FOUND"


class OrderNotPendingError(ConflictError):
    """Raised when a supplier tries to approve or decline an order
    that isn't (or is no longer) PENDING_SUPPLIER_APPROVAL -- e.g.
    already approved, already declined. A real, honest rejection
    rather than silently allowing a second decision to overwrite the
    first."""

    code = "ORDER_NOT_PENDING"


class OrderNotConfirmedError(ConflictError):
    """Raised when a supplier tries to cancel an order that isn't
    CONFIRMED -- a still-PENDING order is cancelled through decline
    (or the business's own cancel_order_by_business), and an already
    DECLINED/CANCELLED order is already terminal. This is
    specifically the "already confirmed, now walking it back" door,
    nothing else (see cancellation_service.py's own module
    docstring)."""

    code = "ORDER_NOT_CONFIRMED"


class DigitalPaymentCancellationNotSupportedError(AppError):
    """Mirrors domains.network.orders' own error of the same name --
    genuinely unreachable today since PAYFAST orders can't exist yet,
    kept as a real, deliberate guard rather than silent trust. See
    that error's own docstring for the full reasoning; duplicated
    here rather than imported, same per-domain error ownership
    already established throughout this codebase."""

    status_code = 409
    code = "DIGITAL_PAYMENT_CANCELLATION_NOT_SUPPORTED"
