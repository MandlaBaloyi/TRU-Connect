"""
SupplierProfileImageService tests. Uses a FakeMediaProvider
(implementing the real MediaProvider interface) instead of
CloudinaryMediaProvider -- same decoupling payoff, and same no-network
constraint, as products/test_product_media_service.py, which this file
mirrors.

MODERATION DEFAULTS OFF here (matching the dev .env's
CLOUDINARY_MODERATION_ENABLED=false), so a registered image is trusted
and promoted onto SupplierProfile immediately. The `moderation_on`
fixture flips it for the PENDING + webhook-lifecycle cases.
"""
from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token

from src.domains.supplier.supplier_profile.models.supplier_profile import VisibleImageSource
from src.domains.supplier.supplier_profile.models.supplier_profile_image import ProfileImageSlot
from src.domains.supplier.supplier_profile.repositories.supplier_profile_image_repository import (
    SupplierProfileImageRepository,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.domains.supplier.supplier_profile.services import supplier_profile_image_service
from src.domains.supplier.supplier_profile.services.errors import ProfileValidationError
from src.core.exceptions import NotFoundError
from src.shared.media import folder_naming
from src.shared.media.errors import PhotoLimitExceededError
from src.shared.media.mixins import MediaScanStatus
from src.shared.media.providers.provider import MediaProvider, ScanResult, SignedUpload, UploadedAsset


class FakeMediaProvider(MediaProvider):
    def __init__(self, moderation_enabled: bool = False):
        self._moderation_enabled = moderation_enabled
        self.deleted_public_ids: list[str] = []
        self.signed_calls: list[str] = []

    def upload_asset(self, public_id, file_bytes, max_dimension_px=1600, asset_folder="tru_connect/fake", resource_type="image"):
        return UploadedAsset(
            public_id=public_id,
            secure_url=f"https://res.cloudinary.com/test/{public_id}.jpg",
            resource_type=resource_type,
            format="jpg",
            width=800,
            height=600,
            bytes=len(file_bytes),
        )

    def generate_signed_upload(self, public_id: str, max_dimension_px: int = 1600, asset_folder: str = "tru_connect/fake") -> SignedUpload:
        self.signed_calls.append(public_id)
        return SignedUpload(
            cloud_name="test_cloud",
            api_key="test_key",
            timestamp=1_700_000_000,
            signature="fake_signature",
            public_id=public_id,
            upload_url="https://api.cloudinary.com/v1_1/test_cloud/image/upload",
            allowed_formats="jpg,jpeg,png,webp",
            transformation="c_limit,w_1600,h_1600,q_auto",
            notification_url="",
            moderation="perception_point" if self._moderation_enabled else "",
            asset_folder=asset_folder,
        )

    def verify_webhook_signature(self, raw_body: str, timestamp: str, signature: str) -> bool:
        return signature == "valid_signature"

    def parse_scan_result(self, payload: dict) -> ScanResult:
        return ScanResult(public_id=payload["public_id"], status=payload["status"], provider="fake")

    def delete_asset(self, public_id: str) -> None:
        self.deleted_public_ids.append(public_id)

    def delete_assets(self, public_ids) -> None:
        self.deleted_public_ids.extend(public_ids)

    def delete_folder(self, folder_path: str) -> None:
        pass

    def is_moderation_enabled(self) -> bool:
        return self._moderation_enabled


@pytest.fixture()
def fake_provider(monkeypatch):
    provider = FakeMediaProvider(moderation_enabled=False)
    monkeypatch.setattr(supplier_profile_image_service, "get_media_provider", lambda: provider)
    return provider


@pytest.fixture()
def moderation_on(monkeypatch):
    provider = FakeMediaProvider(moderation_enabled=True)
    monkeypatch.setattr(supplier_profile_image_service, "get_media_provider", lambda: provider)
    return provider


def _signed_public_id(profile_id, slot: str) -> str:
    return supplier_profile_image_service.request_upload_signature(profile_id, slot).public_id


# --- request_upload_signature --------------------------------------------


def test_signature_public_id_is_scoped_to_the_suppliers_profile_folder(
    fake_provider, make_supplier, make_supplier_profile
):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    signed = supplier_profile_image_service.request_upload_signature(profile.id, "cover")

    assert signed.public_id.startswith(folder_naming.supplier_profile_folder(profile.id) + "/cover-")
    assert folder_naming.is_supplier_profile_asset(signed.public_id)


def test_signature_rejects_unknown_slot(fake_provider, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    with pytest.raises(ProfileValidationError):
        supplier_profile_image_service.request_upload_signature(profile.id, "banner")


def test_signature_creates_an_upload_intent(fake_provider, make_supplier, make_supplier_profile):
    from src.shared.media.intents.models import MediaUploadIntentStatus
    from src.shared.media.intents.repositories import MediaUploadIntentRepository

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    signed = supplier_profile_image_service.request_upload_signature(profile.id, "profile")

    intent = MediaUploadIntentRepository.get_by_public_id(signed.public_id)
    assert intent is not None
    assert intent.status == MediaUploadIntentStatus.ISSUED.value
    assert intent.account_id == profile.id


# --- register_uploaded_image (moderation OFF -> immediate promote) --------


def test_register_promotes_cover_url_onto_the_profile(fake_provider, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    public_id = _signed_public_id(profile.id, "cover")

    image = supplier_profile_image_service.register_uploaded_image(
        profile.id, "cover", public_id, "https://res.cloudinary.com/x/cover.jpg", "image", "jpg", 1600, 500, 40_000
    )

    assert image.scan_status == MediaScanStatus.APPROVED.value
    refreshed = SupplierProfileRepository.get_by_id(profile.id)
    assert refreshed.cover_image_url == "https://res.cloudinary.com/x/cover.jpg"


def test_register_profile_photo_also_sets_visible_image_source_to_business(
    fake_provider, make_supplier, make_supplier_profile
):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier, visible_image_source=VisibleImageSource.NONE)
    public_id = _signed_public_id(profile.id, "profile")

    supplier_profile_image_service.register_uploaded_image(
        profile.id, "profile", public_id, "https://res.cloudinary.com/x/me.jpg", "image", "jpg", 800, 800, 30_000
    )

    refreshed = SupplierProfileRepository.get_by_id(profile.id)
    assert refreshed.business_image_url == "https://res.cloudinary.com/x/me.jpg"
    assert refreshed.visible_image_source == VisibleImageSource.BUSINESS


def test_register_rejects_public_id_outside_the_signed_folder(
    fake_provider, make_supplier, make_supplier_profile
):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    wrong = "tru_connect/suppliers/someone-else/profile/profile-hacked"

    with pytest.raises(NotFoundError):
        supplier_profile_image_service.register_uploaded_image(
            profile.id, "profile", wrong, "https://x/hacked.jpg", "image", "jpg", 100, 100, 500
        )


def test_register_rejects_and_cleans_up_oversized_file(fake_provider, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    public_id = _signed_public_id(profile.id, "cover")
    oversized = 100 * 1024 * 1024  # 100MB, well over FREE's 3MB

    with pytest.raises(PhotoLimitExceededError):
        supplier_profile_image_service.register_uploaded_image(
            profile.id, "cover", public_id, "https://x/big.jpg", "image", "jpg", 100, 100, oversized
        )

    assert public_id in fake_provider.deleted_public_ids
    assert SupplierProfileImageRepository.get_by_public_id(public_id) is None


def test_second_upload_to_same_slot_supersedes_the_first(fake_provider, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    first_id = _signed_public_id(profile.id, "cover")
    supplier_profile_image_service.register_uploaded_image(
        profile.id, "cover", first_id, "https://x/first.jpg", "image", "jpg", 1600, 500, 10_000
    )
    second_id = _signed_public_id(profile.id, "cover")
    supplier_profile_image_service.register_uploaded_image(
        profile.id, "cover", second_id, "https://x/second.jpg", "image", "jpg", 1600, 500, 10_000
    )

    assert SupplierProfileImageRepository.get_by_public_id(first_id) is None  # soft-deleted
    assert first_id in fake_provider.deleted_public_ids
    live = SupplierProfileImageRepository.get_current_for_slot(profile.id, "cover")
    assert live.cloudinary_public_id == second_id
    assert SupplierProfileRepository.get_by_id(profile.id).cover_image_url == "https://x/second.jpg"


def test_register_marks_the_intent_registered(fake_provider, make_supplier, make_supplier_profile):
    from src.shared.media.intents.models import MediaUploadIntentStatus
    from src.shared.media.intents.repositories import MediaUploadIntentRepository

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    public_id = _signed_public_id(profile.id, "profile")

    supplier_profile_image_service.register_uploaded_image(
        profile.id, "profile", public_id, "https://x/me.jpg", "image", "jpg", 800, 800, 20_000
    )

    intent = MediaUploadIntentRepository.get_by_public_id(public_id)
    assert intent.status == MediaUploadIntentStatus.REGISTERED.value


# --- remove_image -------------------------------------------------------


def test_remove_image_clears_the_url_column(fake_provider, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    public_id = _signed_public_id(profile.id, "profile")
    supplier_profile_image_service.register_uploaded_image(
        profile.id, "profile", public_id, "https://x/me.jpg", "image", "jpg", 800, 800, 20_000
    )

    supplier_profile_image_service.remove_image(profile.id, "profile")

    refreshed = SupplierProfileRepository.get_by_id(profile.id)
    assert refreshed.business_image_url is None
    assert refreshed.visible_image_source == VisibleImageSource.NONE
    assert SupplierProfileImageRepository.get_current_for_slot(profile.id, "profile") is None


# --- apply_scan_result (moderation ON -> webhook lifecycle) -------------


def test_pending_image_is_not_promoted_until_scan_approves(moderation_on, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    public_id = _signed_public_id(profile.id, "cover")

    image = supplier_profile_image_service.register_uploaded_image(
        profile.id, "cover", public_id, "https://x/pending.jpg", "image", "jpg", 1600, 500, 10_000
    )
    assert image.scan_status == MediaScanStatus.PENDING.value
    assert SupplierProfileRepository.get_by_id(profile.id).cover_image_url is None

    supplier_profile_image_service.apply_scan_result(
        ScanResult(public_id=public_id, status="APPROVED", provider="cloudinary")
    )

    assert SupplierProfileRepository.get_by_id(profile.id).cover_image_url == "https://x/pending.jpg"


def test_apply_scan_result_rejected_leaves_url_unset(moderation_on, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    public_id = _signed_public_id(profile.id, "cover")
    supplier_profile_image_service.register_uploaded_image(
        profile.id, "cover", public_id, "https://x/bad.jpg", "image", "jpg", 1600, 500, 10_000
    )

    supplier_profile_image_service.apply_scan_result(
        ScanResult(public_id=public_id, status="REJECTED", provider="cloudinary")
    )

    image = SupplierProfileImageRepository.get_by_public_id(public_id)
    assert image.scan_status == MediaScanStatus.REJECTED.value
    assert SupplierProfileRepository.get_by_id(profile.id).cover_image_url is None


def test_apply_scan_result_is_idempotent(moderation_on, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    public_id = _signed_public_id(profile.id, "cover")
    supplier_profile_image_service.register_uploaded_image(
        profile.id, "cover", public_id, "https://x/x.jpg", "image", "jpg", 1600, 500, 10_000
    )
    supplier_profile_image_service.apply_scan_result(ScanResult(public_id=public_id, status="APPROVED", provider="c"))
    # A retried/duplicate delivery now claiming REJECTED must not win.
    supplier_profile_image_service.apply_scan_result(ScanResult(public_id=public_id, status="REJECTED", provider="c"))

    image = SupplierProfileImageRepository.get_by_public_id(public_id)
    assert image.scan_status == MediaScanStatus.APPROVED.value


def test_apply_scan_result_for_unknown_public_id_is_a_safe_no_op(fake_provider, db_session):
    supplier_profile_image_service.apply_scan_result(
        ScanResult(public_id="tru_connect/suppliers/nowhere/profile/profile-ghost", status="APPROVED", provider="c")
    )


# --- HTTP surface (one end-to-end pass through the route) ---------------


def test_signature_endpoint_returns_product_media_shaped_payload(
    fake_provider, client, make_supplier, make_supplier_profile
):
    supplier = make_supplier("img-api@example.com")
    make_supplier_profile(supplier, business_name="Img API Co")
    headers = {"Authorization": f"Bearer {create_access_token(identity=str(supplier.id), additional_claims={'role': 'supplier'})}"}

    resp = client.post(
        "/api/v1/supplier-discovery/my-profile/images/upload-signature",
        json={"slot": "cover"},
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert {"cloud_name", "api_key", "timestamp", "signature", "public_id", "upload_url", "asset_folder"} <= data.keys()
    assert "/profile/cover-" in data["public_id"]
