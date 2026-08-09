"""Business Profile service-layer exceptions."""
from __future__ import annotations


class BusinessProfileError(Exception):
    """Base for every Business Profile service error."""


class BusinessProfileValidationError(BusinessProfileError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field
