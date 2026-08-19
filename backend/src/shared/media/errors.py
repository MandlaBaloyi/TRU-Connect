"""
shared.media exceptions -- all real src.core.exceptions.AppError
subclasses, same convention as every other domain.
"""
from __future__ import annotations

from src.core.exceptions import AppError, ValidationError


class PhotoLimitExceededError(ValidationError):
    code = "PHOTO_LIMIT_EXCEEDED"


class InvalidWebhookSignatureError(AppError):
    status_code = 401
    code = "INVALID_WEBHOOK_SIGNATURE"


class MediaNotFoundError(AppError):
    status_code = 404
    code = "MEDIA_NOT_FOUND"
