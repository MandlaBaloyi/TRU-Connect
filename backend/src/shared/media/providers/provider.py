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
from typing import List, Optional


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
    # "perception_point" when malware scanning is active for this
    # upload, "" when it isn't -- see MediaConfig.moderation_enabled's
    # own docstring for why this is a real, deliberate toggle rather
    # than hardcoded on.
    moderation: str
    # NOT the same field as public_id's own path, even though it's
    # built from the identical string -- see generate_signed_upload's
    # own docstring for why these are two genuinely independent
    # Cloudinary concepts. Must be echoed exactly by the client's own
    # direct upload, same signature rule as every other field here.
    asset_folder: str


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
    def generate_signed_upload(self, public_id: str, max_dimension_px: int, asset_folder: str) -> SignedUpload:
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
        sure what's actually stored stays small every time.

        asset_folder IS NOT THE SAME THING AS public_id's OWN PATH,
        even though the caller passes the identical string for both --
        a real gap found during review: public_id controls the
        asset's permanent URL, asset_folder controls where it actually
        shows up in Cloudinary's browsable Media Library UI. Omitting
        this (as this codebase did until this fix) means every upload
        is still find-able by search but invisible in the Folders
        tree on any Dynamic-Folder-Mode account -- the default for
        every Cloudinary account created since June 2024."""

    @abstractmethod
    def upload_asset(
        self, public_id: str, file_bytes: bytes, max_dimension_px: int, asset_folder: str, resource_type: str = "image"
    ) -> UploadedAsset:
        """Uploads bytes THIS BACKEND ALREADY HOLDS -- the bulk import
        exception to "Flask never carries image bytes". Still never
        the general case: single-product photo upload continues to use
        generate_signed_upload, never this. Same ingest-time
        compression via max_dimension_px, and same asset_folder
        requirement, as generate_signed_upload."""

    @abstractmethod
    def is_moderation_enabled(self) -> bool:
        """Whether malware scanning is actually active for uploads
        right now -- a real, deliberate config toggle (see
        MediaConfig.moderation_enabled's own docstring), not always
        True. Callers (product_media_service) use this to decide
        whether newly registered media should wait for a real scan
        result or be immediately trusted -- see that module's own
        register_uploaded_media docstring for why leaving something
        PENDING with moderation turned off would mean it's NEVER
        approved, not a safe default."""

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
        database row pointing at it. Single-item -- the deleted-product
        sweep (products/jobs/deleted_product_media_sweep.py) uses
        delete_assets below instead, batching many at once."""

    @abstractmethod
    def delete_assets(self, public_ids: List[str]) -> None:
        """Batch delete -- ONE real network call handles MANY assets,
        used by the deleted-product sweep instead of calling
        delete_asset once per photo. Confirmed against the real
        Cloudinary Admin API's own delete_resources during review: this
        is a genuinely different operation from delete_asset (single-
        item), not the same call looped internally by the SDK."""

    @abstractmethod
    def delete_folder(self, folder_path: str) -> None:
        """Confirmed directly against the real Cloudinary SDK's own
        docstring during review: the folder must ALREADY be empty --
        this does NOT cascade-delete its contents. Always call
        delete_assets for everything inside a folder FIRST, this
        second and only once that's done."""
