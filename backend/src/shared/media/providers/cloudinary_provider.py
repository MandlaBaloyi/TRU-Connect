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

INGEST-TIME COMPRESSION -- every upload (signed or backend-initiated)
carries a `transformation` param capping the STORED dimensions
(c_limit,w_X,h_X,q_auto), not just the accepted upload size. This is
the real fix for "a ZIP full of real phone photos will still be huge
even compressed" (raised during review): the size cap on what's
ACCEPTED and the size of what's actually STORED are two different
numbers, and only the second one matters for real Cloudinary cost.
q_auto additionally lets Cloudinary pick the best quality/compression
tradeoff automatically, rather than storing at a fixed quality that's
either wasteful or visibly degraded.
"""
from __future__ import annotations

import time
from typing import Optional

import cloudinary
import cloudinary.uploader
import cloudinary.utils

from src.shared.media.config.media_config import MediaConfig
from src.shared.media.providers.provider import MediaProvider, ScanResult, SignedUpload, UploadedAsset

UPLOAD_URL_TEMPLATE = "https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

# Kept narrow and fixed for now -- widened only if a real future
# consumer (WebP delivery preference, etc.) needs it. Products'
# max_image_upload_bytes (the ACCEPTED size, a different number from
# the STORED size this file controls) lives in products/tiers/, not
# here -- this list is a format allowlist, not a size limit.
ALLOWED_IMAGE_FORMATS = ("jpg", "jpeg", "png", "webp")


def _incoming_transformation(max_dimension_px: int) -> str:
    return f"c_limit,w_{max_dimension_px},h_{max_dimension_px},q_auto"


class CloudinaryMediaProvider(MediaProvider):
    def __init__(self, config: MediaConfig):
        self._config = config
        cloudinary.config(
            cloud_name=config.cloud_name,
            api_key=config.api_key,
            api_secret=config.api_secret,
            secure=True,
        )

    def generate_signed_upload(self, public_id: str, max_dimension_px: int) -> SignedUpload:
        allowed_formats = ",".join(ALLOWED_IMAGE_FORMATS)
        transformation = _incoming_transformation(max_dimension_px)
        params = {
            "timestamp": int(time.time()),
            "public_id": public_id,
            "allowed_formats": allowed_formats,
            "transformation": transformation,
        }
        notification_url = self._config.notification_url
        if notification_url:
            # Only included in the signature when actually configured --
            # an empty notification_url would still get SIGNED (and
            # then rejected by Cloudinary as an invalid callback URL)
            # if included unconditionally.
            params["notification_url"] = notification_url

        signed = cloudinary.utils.sign_request(dict(params), {})
        return SignedUpload(
            cloud_name=self._config.cloud_name,
            api_key=signed["api_key"],
            timestamp=params["timestamp"],
            signature=signed["signature"],
            public_id=public_id,
            upload_url=UPLOAD_URL_TEMPLATE.format(cloud_name=self._config.cloud_name),
            allowed_formats=allowed_formats,
            transformation=transformation,
            notification_url=notification_url,
        )

    def upload_asset(
        self, public_id: str, file_bytes: bytes, max_dimension_px: int, resource_type: str = "image"
    ) -> UploadedAsset:
        upload_kwargs = {}
        if self._config.notification_url:
            upload_kwargs["notification_url"] = self._config.notification_url

        result = cloudinary.uploader.upload(
            file_bytes,
            public_id=public_id,
            resource_type=resource_type,
            transformation=_incoming_transformation(max_dimension_px),
            **upload_kwargs,
        )
        return UploadedAsset(
            public_id=result["public_id"],
            secure_url=result["secure_url"],
            resource_type=result.get("resource_type", resource_type),
            format=result.get("format"),
            width=result.get("width"),
            height=result.get("height"),
            bytes=result.get("bytes"),
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

        # CONFIRMED WITH A REAL PAYLOAD DURING DEVICE TESTING, NOT
        # ASSUMED -- Cloudinary calls the SAME notification_url for its
        # "upload" notification (fires the instant the file lands,
        # before any scanning has happened) as it does for a real
        # moderation result. An "upload" notification carries no
        # moderation_status at all -- previously, that meant this
        # method fell through to the ERROR branch below, which is
        # factually wrong: nothing failed a scan, no scan has happened
        # yet. "IGNORED" is a genuine third outcome (see ScanResult's
        # own docstring / apply_scan_result's own handling) --
        # deliberately distinct from "ERROR" so the caller can
        # correctly do nothing rather than misfile the media.
        if raw_status is None and payload.get("notification_type") != "moderation":
            return ScanResult(public_id=public_id, status="IGNORED", provider="cloudinary", raw_result=str(payload))

        status_map = {"approved": "APPROVED", "rejected": "REJECTED"}
        status = status_map.get((raw_status or "").lower(), "ERROR")

        return ScanResult(public_id=public_id, status=status, provider="cloudinary", raw_result=str(payload))

    def delete_asset(self, public_id: str) -> None:
        cloudinary.uploader.destroy(public_id)
