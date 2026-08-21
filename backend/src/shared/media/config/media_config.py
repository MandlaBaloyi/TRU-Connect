"""
MediaConfig -- ONLY what's genuinely universal across every future
media consumer: Cloudinary credentials and signature timing. Nothing
here is a business rule.

WHAT USED TO LIVE HERE AND WHY IT DOESN'T ANYMORE: photo-count limits,
allowed formats, and max file size were originally defined in this
file, discovered during review to be a real leak -- those are
Products-specific decisions (a profile photo isn't tier-gated by
count, a verification document isn't always an image, a future
domain's size ceiling has nothing to do with Products' own). Each
consuming domain now owns its own limits entirely -- see
products/tiers/ for Products' own numbers. This file only holds what
would be identical no matter which domain is uploading.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MediaConfig:
    cloud_name: str
    api_key: str
    api_secret: str
    # Cloudinary's own signed-upload timestamp window -- a signature
    # older than this is rejected by Cloudinary itself, independent of
    # anything this backend does. 10 minutes is generous for a mobile
    # upload that might sit on a slow connection.
    signature_valid_for_seconds: int = 600
    # The public URL Cloudinary calls back to once a scan finishes --
    # e.g. https://your-tunnel.ngrok-free.app while developing locally,
    # a real domain once deployed. Genuinely universal, not a
    # Products-specific setting: every domain's uploads notify the
    # SAME one webhook endpoint (/api/v1/media/webhooks/cloudinary-scan),
    # which then routes internally by folder (see webhooks/webhook_service.py's
    # own docstring) -- that's exactly why this lives here and not in
    # products/tiers/. Empty by default; a signed upload simply won't
    # request a callback if this isn't configured, matching every other
    # piece of this build that stays honest about what isn't wired up
    # yet rather than sending a broken value.
    webhook_base_url: str = ""

    @classmethod
    def from_env(cls) -> "MediaConfig":
        return cls(
            cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
            api_key=os.environ.get("CLOUDINARY_API_KEY", ""),
            api_secret=os.environ.get("CLOUDINARY_API_SECRET", ""),
            webhook_base_url=os.environ.get("CLOUDINARY_WEBHOOK_BASE_URL", "").rstrip("/"),
        )

    @property
    def notification_url(self) -> str:
        if not self.webhook_base_url:
            return ""
        return f"{self.webhook_base_url}/api/v1/media/webhooks/cloudinary-scan"
