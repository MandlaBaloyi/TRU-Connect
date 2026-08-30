"""
itn_service -- NOT IMPLEMENTED YET. Will verify and process PayFast's
own ITN (Instant Transaction Notification) callback, the moment
payfast_provider.py itself is real.

THE PATTERN TO MIRROR, proven working in shared/media/webhooks/
webhook_service.py -- confirmed and referenced deliberately rather
than inventing a new shape:
- Verify the caller is genuinely PayFast BEFORE trusting anything in
  the payload (PayFast signs ITN payloads; verification happens via
  the provider, not here directly -- see PaymentProvider's own
  interface for where a verify_webhook_signature-style method would
  live once needed).
- MUST be idempotent -- PayFast retries a notification if it doesn't
  receive a 200 quickly enough. A duplicate delivery transitioning an
  already-SUBMITTED order a second time must be a safe no-op, never a
  double-processed order or a double-sent confirmation.
- Only a VERIFIED server-to-server notification ever transitions an
  order from AWAITING_PAYMENT to SUBMITTED -- never the business's own
  client-side "I paid" claim on return from the redirect, exactly like
  Cloudinary's own webhook is the only trusted source for a media scan
  result, never the client's own upload-succeeded claim.
"""
from __future__ import annotations


def handle_itn_notification(raw_body: str, signature: str) -> None:
    raise NotImplementedError(
        "PayFast ITN handling isn't wired yet. See this file's own module docstring for the pattern to follow, "
        "already proven in shared/media/webhooks/webhook_service.py."
    )
