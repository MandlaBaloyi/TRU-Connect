"""
Cloudinary scan-callback webhook. NO @fully_authenticated -- Cloudinary
itself is calling this, not a logged-in TRU Connect user. The HMAC
signature (verified inside webhook_service.handle_scan_webhook) is the
ONLY authorization this endpoint has, which is exactly why that
verification is not optional and not best-effort.

Always returns 200 on anything short of a bad signature -- webhook
senders retry aggressively on non-2xx, and retrying a webhook whose
public_id this backend doesn't recognise, or whose handler already
no-op'd because the row is already terminal, would just be wasted
retries for both sides.
"""
from __future__ import annotations

from flask import Blueprint, request

from src.core.responses import error_response, success_response
from src.shared.media.errors import InvalidWebhookSignatureError
from src.shared.media.webhooks.webhook_service import handle_scan_webhook

media_webhooks_bp = Blueprint("media_webhooks", __name__)


@media_webhooks_bp.route("/api/v1/media/webhooks/cloudinary-scan", methods=["POST"])
def cloudinary_scan_callback():
    raw_body = request.get_data(as_text=True)
    timestamp = request.headers.get("X-Cld-Timestamp", "")
    signature = request.headers.get("X-Cld-Signature", "")

    try:
        result = handle_scan_webhook(raw_body, timestamp, signature)
    except InvalidWebhookSignatureError:
        return error_response(message="Invalid signature.", status_code=401, code="INVALID_WEBHOOK_SIGNATURE")
    except (ValueError, TypeError):
        # Malformed JSON body -- genuinely bad request, not a retry-me
        # situation.
        return error_response(message="Malformed payload.", status_code=400)

    return success_response(data={"public_id": result.public_id, "status": result.status})
