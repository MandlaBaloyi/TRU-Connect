"""
CloudinaryMediaProvider -- the ONLY file in this codebase that imports
the `cloudinary` package. Everything else depends on MediaProvider
(provider.py), never this class directly, never the SDK directly.

SIGNING IS 100% LOCAL, NO NETWORK CALL -- cloudinary.utils.sign_request
computes an HMAC locally using the api_secret this process holds; it
never talks to Cloudinary's servers. This matters for THIS backend's
own test suite: generate_signed_upload is fully unit-testable without
any network access, and this environment's own network policy doesn't
allow reaching api.cloudinary.com anyway -- confirmed directly, not
assumed, before building this file. The only genuinely networked half
of an upload (the client posting bytes straight to Cloudinary) never
touches this backend at all, by design -- see generate_signed_upload's
own docstring on the SignedUpload contract.

WEBHOOK VERIFICATION USES CLOUDINARY'S OWN SDK FUNCTION
(verify_notification_signature), not a hand-rolled HMAC comparison --
confirmed against the actual installed SDK's source before writing
this: it reads api_secret from the global cloudinary.config(), takes
the raw body/timestamp/signature, and has REPLAY PROTECTION built in
(rejects a signature older than `valid_for` seconds, 7200 by default;
this class passes MediaConfig's own signature_valid_for_seconds
instead so the two use the same window as the upload signature).
"""
from __future__ import annotations

import time
from typing import Optional

import cloudinary
import cloudinary.uploader
import cloudinary.utils

from src.shared.media.config import MediaConfig
from src.shared.media.provider import MediaProvider, ScanResult, SignedUpload

UPLOAD_URL_TEMPLATE = "https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"


class CloudinaryMediaProvider(MediaProvider):
    def __init__(self, config: MediaConfig):
        self._config = config
        cloudinary.config(
            cloud_name=config.cloud_name,
            api_key=config.api_key,
            api_secret=config.api_secret,
            secure=True,
        )

    def generate_signed_upload(self, public_id: str) -> SignedUpload:
        allowed_formats = ",".join(self._config.allowed_formats)
        params = {
            "timestamp": int(time.time()),
            "public_id": public_id,
            "allowed_formats": allowed_formats,
        }
        signed = cloudinary.utils.sign_request(dict(params), {})
        return SignedUpload(
            cloud_name=self._config.cloud_name,
            api_key=signed["api_key"],
            timestamp=params["timestamp"],
            signature=signed["signature"],
            public_id=public_id,
            upload_url=UPLOAD_URL_TEMPLATE.format(cloud_name=self._config.cloud_name),
            allowed_formats=allowed_formats,
        )

    def verify_webhook_signature(self, raw_body: str, timestamp: str, signature: str) -> bool:
        if not timestamp or not signature:
            return False
        try:
            return cloudinary.utils.verify_notification_signature(
                raw_body, timestamp, signature, valid_for=self._config.signature_valid_for_seconds
            )
        except Exception:
            # Malformed timestamp, missing configured secret, etc. --
            # ANY failure here means "not verified", never "assume ok".
            return False

    def parse_scan_result(self, payload: dict) -> ScanResult:
        public_id = payload.get("public_id", "")

        # Defensive against real, documented payload variation across
        # Cloudinary moderation add-on versions -- confirmed two
        # different shapes exist in Cloudinary's own published
        # examples: a flat `moderation_status` field, and a
        # `moderation` array with `[0].status`. Cloudinary's own docs
        # explicitly warn integrations to stay forward-compatible with
        # unknown/changed fields rather than assume one fixed shape.
        raw_status: Optional[str] = payload.get("moderation_status")
        if raw_status is None:
            moderation = payload.get("moderation")
            if isinstance(moderation, list) and moderation:
                raw_status = moderation[0].get("status")

        status_map = {"approved": "APPROVED", "rejected": "REJECTED"}
        status = status_map.get((raw_status or "").lower(), "ERROR")

        return ScanResult(public_id=public_id, status=status, provider="cloudinary", raw_result=str(payload))

    def delete_asset(self, public_id: str) -> None:
        cloudinary.uploader.destroy(public_id)
