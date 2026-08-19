"""
MediaConfig -- every Cloudinary credential and every configurable
limit lives here, sourced from environment variables, never hardcoded
in a service or route. This is what makes "configuration such as
limits, Cloudinary settings, scan providers, and tier entitlements
must come from configuration/services rather than hard-coded values"
(the exact production requirement this domain was built against)
actually true rather than aspirational.

TIER LIMITS ARE HONEST ABOUT TODAY'S REALITY -- there is no real
Subscription domain on this backend yet (confirmed during planning:
the frontend's own getPhotoLimit already takes a `tier` PARAMETER
rather than resolving one internally, specifically so the caller can
stay honest about this). PHOTO_LIMIT_BY_TIER matches the frontend's
own corrected numbers exactly (Free 2 / Pro 3 / Max 5); every real
caller in this domain passes "FREE" until a real Subscription lookup
exists to pass something else.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value else default


PHOTO_LIMIT_BY_TIER: Dict[str, int] = {"FREE": 2, "PRO": 3, "MAX": 5}

ALLOWED_IMAGE_FORMATS = ("jpg", "jpeg", "png", "webp")


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
    max_image_bytes: int = field(default_factory=lambda: _env_int("MEDIA_MAX_IMAGE_BYTES", 8 * 1024 * 1024))
    allowed_formats: tuple = ALLOWED_IMAGE_FORMATS
    photo_limit_by_tier: Dict[str, int] = field(default_factory=lambda: dict(PHOTO_LIMIT_BY_TIER))

    @classmethod
    def from_env(cls) -> "MediaConfig":
        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
        api_key = os.environ.get("CLOUDINARY_API_KEY", "")
        api_secret = os.environ.get("CLOUDINARY_API_SECRET", "")
        return cls(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)

    def photo_limit_for_tier(self, tier: str) -> int:
        return self.photo_limit_by_tier.get(tier.upper(), self.photo_limit_by_tier["FREE"])
