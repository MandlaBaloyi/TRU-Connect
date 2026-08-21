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
    transformation: str
    # Empty string when webhook_base_url isn't configured (e.g. no
    # tunnel running yet) -- signed WITHOUT it in that case, so an
    # upload still succeeds; it just never gets a scan-result callback,
    # matching this whole build's own "stay honest about what isn't
    # wired up yet" discipline rather than sending Cloudinary a
    # notification_url that would only ever fail to be reached.
    notification_url: str


@dataclass(frozen=True)
class ScanResult:
    """The parsed, verified result of a webhook call -- provider-
    agnostic on purpose, same reasoning as SignedUpload.

    status is "IGNORED" for a webhook that arrived from the provider
    but carries no real scan verdict at all -- confirmed necessary
    during real device testing: Cloudinary calls the SAME
    notification_url for its "upload" notification (fires the instant
    a file lands, before any scanning happens) as it does for a real
    moderation result. Treating that as "ERROR" would falsely tell a
    supplier their photo failed a scan it was never put through --
    "IGNORED" is a genuine, deliberately distinct third outcome the
    caller (apply_scan_result) uses to correctly do nothing."""

    public_id: str
    status: str  # "APPROVED" | "REJECTED" | "ERROR" | "IGNORED"
    provider: str
    raw_result: Optional[str] = None


@dataclass(frozen=True)
class UploadedAsset:
    """The result of THIS BACKEND uploading bytes it already has --
    distinct from SignedUpload (which authorizes a CLIENT's own direct
    upload). Used by bulk import specifically: a supplier's images
    arrive bundled inside one ZIP uploaded to this backend, not as
    individual client-initiated signed uploads the way single-product
    photos work. The backend genuinely holds the bytes in that one
    case, so it uploads them itself."""

    public_id: str
    secure_url: str
    resource_type: str
    format: Optional[str]
    width: Optional[int]
    height: Optional[int]
    bytes: Optional[int]


class MediaProvider(ABC):
    @abstractmethod
    def generate_signed_upload(self, public_id: str, max_dimension_px: int) -> SignedUpload:
        """Authorizes a direct-to-provider upload for EXACTLY this
        public_id -- the caller (product_media_service) has already
        verified ownership and built a supplier/product-scoped path
        before this is ever called; this method doesn't know or care
        what a "product" is.

        max_dimension_px caps what actually gets STORED, not what's
        accepted -- an incoming transformation applied at upload time,
        so a phone's full-resolution original is resized/compressed on
        ingest regardless of how large the source file was. This is
        the real answer to "won't a ZIP full of real photos blow past
        any size cap" -- the fix isn't a bigger allowance, it's making
        sure what's actually stored stays small every time."""

    @abstractmethod
    def upload_asset(
        self, public_id: str, file_bytes: bytes, max_dimension_px: int, resource_type: str = "image"
    ) -> UploadedAsset:
        """Uploads bytes THIS BACKEND ALREADY HOLDS -- the bulk import
        exception to "Flask never carries image bytes". Still never
        the general case: single-product photo upload continues to use
        generate_signed_upload, never this. Same ingest-time
        compression via max_dimension_px as generate_signed_upload."""

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
