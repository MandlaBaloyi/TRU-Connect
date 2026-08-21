"""
Webhook service -- verifies the caller is genuinely Cloudinary, parses
the scan result, then dispatches to whichever DOMAIN registered
itself as owning that asset's public_id. shared/media still doesn't
know what a "product" is: products/services/product_media_service.py
calls register_scan_result_handler(folder_naming.is_supplier_product_asset,
apply_scan_result) once at app startup (see src/__init__.py).

MATCHER FUNCTIONS, NOT PREFIX STRINGS -- the who-owns-it-first folder
taxonomy (tru_connect/suppliers/{supplier_id}/products/{product_id}/...,
see folder_naming.py's own docstring) means there's no longer a fixed
string every product asset starts with -- supplier_profile_id is a
variable UUID sitting BEFORE the "products" segment. Each domain
supplies its own predicate (public_id -> bool) instead, giving it full
control over how it recognises its own assets regardless of where in
the path that recognition needs to happen.

IDEMPOTENT BY CONSTRUCTION, NOT BY ACCIDENT -- this file itself does
no idempotency check; it's the REGISTERED HANDLER's job (see
product_media_service.apply_scan_result's own docstring) to no-op if
the row it's about to update is already in a terminal state. Webhook
senders retry; a duplicate delivery must never double-process.
"""
from __future__ import annotations

import json
from typing import Callable, List, Tuple

from src.shared.media.providers.composition import get_media_provider
from src.shared.media.errors import InvalidWebhookSignatureError
from src.shared.media.providers.provider import ScanResult

_HANDLERS: List[Tuple[Callable[[str], bool], Callable[[ScanResult], None]]] = []


def register_scan_result_handler(matcher: Callable[[str], bool], handler: Callable[[ScanResult], None]) -> None:
    _HANDLERS.append((matcher, handler))


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

    for matcher, handler in _HANDLERS:
        if matcher(result.public_id):
            handler(result)
            break
    # An unmatched public_id isn't an error -- Cloudinary still needs a
    # 200 so it doesn't retry forever, and a genuinely unrecognised
    # asset (e.g. something uploaded outside this backend's own
    # signed-upload flow) has nothing here to reconcile against.

    return result
