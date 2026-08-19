"""
products service-layer exceptions -- all real src.core.exceptions.
AppError subclasses, letting the app-wide error handler convert them
automatically, same DRY pattern connections/services/errors.py already
documents and follows.
"""
from __future__ import annotations

from src.core.exceptions import NotFoundError, ValidationError


class ProductNotFoundError(NotFoundError):
    """Used for BOTH 'genuinely doesn't exist' and 'exists but belongs
    to a different supplier' -- same IDOR-safety reasoning as every
    other NotFoundError subclass in this codebase. A supplier probing
    another supplier's product id learns nothing more than 404 either
    way."""

    code = "PRODUCT_NOT_FOUND"


class ProductValidationError(ValidationError):
    code = "VALIDATION_ERROR"
