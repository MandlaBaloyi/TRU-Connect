"""
MediaProvider -- the abstract contract every media storage/scanning
backend implements. This is what makes "Cloudinary can be replaced
later without rewriting the Products domain" true rather than a claim:
products/services/product_media_service.py depends on THIS interface,
never on cloudinary_provider.py or the cloudinary package directly.
Swapping providers means writing one new class here and changing one
import at the composition point (get_media_provider() below) -- no
other file in this codebase needs to change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SignedUpload:
    """Everything the client needs to upload DIRECTLY to the media
    provider -- never routed through this backend. cloud_name/api_key
    are not secret; the signature is the proof this backend actually
    authorized this exact upload (this exact public_id, this exact
    timestamp), computed with the api_secret THIS BACKEND holds and
    never sends anywhere."""

    cloud_name: str
    api_key: str
    timestamp: int
    signature: str
    public_id: str
    upload_url: str
    allowed_formats: str


@dataclass(frozen=True)
class ScanResult:
    """The parsed, verified result of a scan-complete webhook --
    provider-agnostic on purpose, same reasoning as SignedUpload."""

    public_id: str
    status: str  # "APPROVED" | "REJECTED" | "ERROR"
    provider: str
    raw_result: Optional[str] = None


class MediaProvider(ABC):
    @abstractmethod
    def generate_signed_upload(self, public_id: str) -> SignedUpload:
        """Authorizes a direct-to-provider upload for EXACTLY this
        public_id -- the caller (product_media_service) has already
        verified ownership and built a supplier/product-scoped path
        before this is ever called; this method doesn't know or care
        what a "product" is."""

    @abstractmethod
    def verify_webhook_signature(self, raw_body: str, timestamp: str, signature: str) -> bool:
        """True only if this request genuinely came from the media
        provider -- an external, unauthenticated caller, so this is
        the ONLY authorization this endpoint has."""

    @abstractmethod
    def parse_scan_result(self, payload: dict) -> ScanResult:
        """Turns the provider's own webhook payload shape into the
        provider-agnostic ScanResult every caller in this codebase
        actually works with."""

    @abstractmethod
    def delete_asset(self, public_id: str) -> None:
        """Used when a registered upload turns out to violate a rule
        this backend enforces after the fact (oversized file) -- never
        leaves an orphaned asset sitting in provider storage with no
        database row pointing at it."""
