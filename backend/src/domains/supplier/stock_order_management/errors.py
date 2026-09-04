"""
domains.supplier.stock_order_management exceptions -- all real
src.core.exceptions.AppError subclasses, same convention as every
other domain in this codebase.
"""
from __future__ import annotations

from src.core.exceptions import ConflictError, NotFoundError


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
