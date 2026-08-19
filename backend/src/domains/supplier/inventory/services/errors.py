"""
inventory service-layer exceptions -- all real src.core.exceptions.
AppError subclasses, same convention as products/services/errors.py.
"""
from __future__ import annotations

from src.core.exceptions import ConflictError, NotFoundError, ValidationError


class ProductNotFoundError(NotFoundError):
    """Raised when the product_id in an inventory request doesn't
    exist, or belongs to a different supplier -- same IDOR-safety
    reasoning as every other NotFoundError in this codebase."""

    code = "PRODUCT_NOT_FOUND"


class InsufficientStockError(ConflictError):
    """Raised when an adjustment would take quantity_on_hand below
    zero -- a real business-state conflict, not a validation-shape
    problem (409, not 422), matching this codebase's own status-code
    convention for "the request is well-formed but the current state
    doesn't allow it"."""

    code = "INSUFFICIENT_STOCK"


class InventoryValidationError(ValidationError):
    code = "VALIDATION_ERROR"
