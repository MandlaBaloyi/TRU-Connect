"""
supplier_profile service-layer exceptions -- all real
src.core.exceptions.AppError subclasses, same DRY pattern
connections/services/errors.py and products/services/errors.py already
document and follow.
"""
from __future__ import annotations

from src.core.exceptions import ValidationError


class ProfileValidationError(ValidationError):
    code = "VALIDATION_ERROR"
