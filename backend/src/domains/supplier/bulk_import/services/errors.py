"""
bulk_import service-layer exceptions.
"""
from __future__ import annotations

from src.core.exceptions import NotFoundError, ValidationError


class ImportJobNotFoundError(NotFoundError):
    code = "IMPORT_JOB_NOT_FOUND"


class ImportUploadValidationError(ValidationError):
    code = "VALIDATION_ERROR"
