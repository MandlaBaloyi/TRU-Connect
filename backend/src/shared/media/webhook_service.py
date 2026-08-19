"""
Webhook service -- verifies the caller is genuinely Cloudinary, parses
the scan result, then dispatches to whichever DOMAIN registered
itself for that asset's folder prefix. shared/media still doesn't
know what a "product" is: products/services/product_media_service.py
calls register_scan_result_handler("tru_connect/products/", ...) once
at app startup (see src/__init__.py), and this file just looks up
which callback owns a given public_id's prefix.

IDEMPOTENT BY CONSTRUCTION, NOT BY ACCIDENT -- this file itself does
no idempotency check; it's the REGISTERED HANDLER's job (see
product_media_service.apply_scan_result's own docstring) to no-op if
the row it's about to update is already in a terminal state. Webhook
senders retry; a duplicate delivery must never double-process.
"""
from __future__ import annotations

import json
from typing import Callable, Dict

from src.shared.media.composition import get_media_provider
from src.shared.media.errors import InvalidWebhookSignatureError
from src.shared.media.provider import ScanResult

_HANDLERS: Dict[str, Callable[[ScanResult], None]] = {}


def register_scan_result_handler(folder_prefix: str, handler: Callable[[ScanResult], None]) -> None:
    _HANDLERS[folder_prefix] = handler


def clear_scan_result_handlers() -> None:
    """Test-only -- avoids handler registrations leaking between test
    modules that each want to test dispatch in isolation."""
    _HANDLERS.clear()


def handle_scan_webhook(raw_body: str, timestamp: str, signature: str) -> ScanResult:
    provider = get_media_provider()
    if not provider.verify_webhook_signature(raw_body, timestamp, signature):
        raise InvalidWebhookSignatureError("Invalid webhook signature.")

    payload = json.loads(raw_body)
    result = provider.parse_scan_result(payload)

    for prefix, handler in _HANDLERS.items():
        if result.public_id.startswith(prefix):
            handler(result)
            break
    # An unmatched prefix isn't an error -- Cloudinary still needs a
    # 200 so it doesn't retry forever, and a genuinely unrecognised
    # asset (e.g. something uploaded outside this backend's own
    # signed-upload flow) has nothing here to reconcile against.

    return result
