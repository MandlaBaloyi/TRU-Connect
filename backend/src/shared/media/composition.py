"""
get_media_provider() -- the ONE place in this codebase that decides
"Cloudinary is the media provider today". Every service that needs
media (product_media_service.py, the webhook route) calls this
function, never `CloudinaryMediaProvider(...)` directly. Swapping
providers later means changing this one function's body.
"""
from __future__ import annotations

from src.shared.media.config import MediaConfig
from src.shared.media.provider import MediaProvider

_provider: MediaProvider | None = None


def get_media_provider() -> MediaProvider:
    global _provider
    if _provider is None:
        from src.shared.media.cloudinary_provider import CloudinaryMediaProvider

        _provider = CloudinaryMediaProvider(MediaConfig.from_env())
    return _provider


def reset_media_provider() -> None:
    """Test-only -- lets each test start from a clean provider instance
    rather than one memoized across the whole test session."""
    global _provider
    _provider = None
