"""
ProductMediaService tests. Uses a FakeMediaProvider (implementing the
real MediaProvider interface) instead of CloudinaryMediaProvider -- the
whole POINT of building that interface was so callers never depend on
Cloudinary directly; this is that decoupling actually paying off; it
also means these tests need no network access at all, matching this
sandbox's own real constraints.
"""
from __future__ import annotations

import pytest

from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_media_repository import ProductMediaRepository
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.domains.supplier.products.services import product_media_service
from src.domains.supplier.products.services.errors import ProductNotFoundError
from src.shared.media import folder_naming
from src.shared.media.errors import PhotoLimitExceededError
from src.shared.media.mixins import MediaScanStatus
from src.shared.media.providers.provider import MediaProvider, ScanResult, SignedUpload


class FakeMediaProvider(MediaProvider):
    def __init__(self):
        self.deleted_public_ids: list[str] = []
        self.signed_calls: list[str] = []

    def upload_asset(self, public_id, file_bytes, max_dimension_px=1600, asset_folder="tru_connect/fake", resource_type="image"):
        from src.shared.media.providers.provider import UploadedAsset
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
            moderation="perception_point",
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
        return True


@pytest.fixture()
def fake_provider(monkeypatch):
    provider = FakeMediaProvider()
    monkeypatch.setattr(product_media_service, "get_media_provider", lambda: provider)
    return provider


def _make_product(profile_id, **overrides):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    defaults = dict(
        supplier_profile_id=profile_id,
        name="Coca-Cola 500ml",
        category=ProductCategory.BEVERAGES,
        price_cents=1200,
        selling_unit=ProductUnit.EACH,
        sku=generate_sku(profile_id),
        product_code=generate_product_code(),
    )
    defaults.update(overrides)
    return SupplierOfferRepository.create(**defaults)


# --- request_upload_signature -------------------------------------------


def test_request_upload_signature_builds_scoped_public_id(fake_provider, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    signed = product_media_service.request_upload_signature(product.id, profile.id)

    assert signed.public_id.startswith(folder_naming.supplier_product_folder(profile.id, product.id) + "/")


def test_request_upload_signature_raises_not_found_for_other_suppliers_product(
    fake_provider, make_supplier, make_supplier_profile
):
    owner = make_supplier("media-owner1@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Media Owner 1")
    other = make_supplier("media-other1@example.com")
    other_profile = make_supplier_profile(other, business_name="Media Other 1")
    product = _make_product(owner_profile.id)

    with pytest.raises(ProductNotFoundError):
        product_media_service.request_upload_signature(product.id, other_profile.id)


def test_request_upload_signature_enforces_free_tier_limit_of_two(
    fake_provider, make_supplier, make_supplier_profile
):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    # Seed 2 already-registered (non-rejected) media rows directly --
    # FREE tier's limit is 2.
    ProductMediaRepository.create_pending(product.id, "existing/1", "https://x/1.jpg", "image", "jpg", 100, 100, 500, 0)
    ProductMediaRepository.create_pending(product.id, "existing/2", "https://x/2.jpg", "image", "jpg", 100, 100, 500, 1)

    with pytest.raises(PhotoLimitExceededError):
        product_media_service.request_upload_signature(product.id, profile.id)


def test_request_upload_signature_rejected_media_does_not_count_against_limit(
    fake_provider, make_supplier, make_supplier_profile
):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    rejected = ProductMediaRepository.create_pending(
        product.id, "existing/rejected", "https://x/r.jpg", "image", "jpg", 100, 100, 500, 0
    )
    ProductMediaRepository.apply_scan_status(rejected, MediaScanStatus.REJECTED.value, "cloudinary", None)

    # Should succeed -- only 0 NON-rejected photos exist, well under
    # the FREE limit of 2.
    signed = product_media_service.request_upload_signature(product.id, profile.id)
    assert signed.public_id


# --- register_uploaded_media ---------------------------------------------


def test_register_uploaded_media_creates_pending_row(fake_provider, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    public_id = folder_naming.supplier_product_folder(profile.id, product.id) + "/abc123"

    media = product_media_service.register_uploaded_media(
        product.id, profile.id, public_id, "https://res.cloudinary.com/x/abc123.jpg", "image", "jpg", 800, 600, 50_000
    )

    assert media.scan_status == MediaScanStatus.PENDING.value
    assert media.cloudinary_public_id == public_id


def test_register_uploaded_media_rejects_public_id_outside_expected_folder(
    fake_provider, make_supplier, make_supplier_profile
):
    """A client claiming a public_id it was never signed for -- must
    be rejected, never trusted at face value."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    wrong_public_id = "tru_connect/suppliers/someone-elses-supplier-id/products/some-product/hacked"

    with pytest.raises(ProductNotFoundError):
        product_media_service.register_uploaded_media(
            product.id, profile.id, wrong_public_id, "https://x/hacked.jpg", "image", "jpg", 100, 100, 500
        )


def test_register_uploaded_media_rejects_and_cleans_up_oversized_file(
    fake_provider, make_supplier, make_supplier_profile
):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    public_id = folder_naming.supplier_product_folder(profile.id, product.id) + "/toobig"
    oversized_bytes = 100 * 1024 * 1024  # 100MB, well over FREE tier's 3MB max (products/tiers/free.py)

    with pytest.raises(PhotoLimitExceededError):
        product_media_service.register_uploaded_media(
            product.id, profile.id, public_id, "https://x/toobig.jpg", "image", "jpg", 100, 100, oversized_bytes
        )

    # The asset must actually get cleaned up from provider storage --
    # never leave an orphan.
    assert public_id in fake_provider.deleted_public_ids
    assert ProductMediaRepository.get_by_public_id(public_id) is None


# --- apply_scan_result (the webhook callback) -----------------------------


def test_apply_scan_result_approves_pending_media(fake_provider, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    public_id = folder_naming.supplier_product_folder(profile.id, product.id) + "/scan-me"
    product_media_service.register_uploaded_media(
        product.id, profile.id, public_id, "https://x/scan-me.jpg", "image", "jpg", 100, 100, 500
    )

    product_media_service.apply_scan_result(ScanResult(public_id=public_id, status="APPROVED", provider="cloudinary"))

    media = ProductMediaRepository.get_by_public_id(public_id)
    assert media.scan_status == MediaScanStatus.APPROVED.value


def test_apply_scan_result_is_idempotent_does_not_reapply_to_terminal_state(
    fake_provider, make_supplier, make_supplier_profile
):
    """The whole point of the idempotency requirement -- a webhook
    retried after already being applied must not change anything."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    public_id = folder_naming.supplier_product_folder(profile.id, product.id) + "/scan-me2"
    product_media_service.register_uploaded_media(
        product.id, profile.id, public_id, "https://x/scan-me2.jpg", "image", "jpg", 100, 100, 500
    )
    product_media_service.apply_scan_result(ScanResult(public_id=public_id, status="APPROVED", provider="cloudinary"))

    # A retried/duplicate webhook delivery, now claiming REJECTED --
    # must NOT override the already-terminal APPROVED state.
    product_media_service.apply_scan_result(ScanResult(public_id=public_id, status="REJECTED", provider="cloudinary"))

    media = ProductMediaRepository.get_by_public_id(public_id)
    assert media.scan_status == MediaScanStatus.APPROVED.value


def test_apply_scan_result_for_unknown_public_id_is_a_safe_no_op(fake_provider, db_session):
    # Must not raise -- an asset this backend never registered (e.g.
    # something outside this domain's own folder prefix) is not an
    # error condition for the webhook to blow up on.
    product_media_service.apply_scan_result(
        ScanResult(public_id="tru_connect/suppliers/nowhere/products/nothing/ghost", status="APPROVED", provider="cloudinary")
    )


def test_real_webhook_sequence_reaches_approved_not_stuck_behind_a_false_error(
    fake_provider, make_supplier, make_supplier_profile
):
    """THE DECISIVE TEST for the real bug found during device testing:
    replays the EXACT two-webhook sequence Cloudinary actually sent
    (an "upload" notification with moderation: [{"status": "pending"}]
    arriving first, followed seconds later by the real "moderation"
    notification with the genuine "approved" verdict) and confirms the
    row correctly ends up APPROVED. Before the fix, the first webhook
    incorrectly wrote a terminal ERROR, and apply_scan_result's own
    correct idempotency guard then blocked the second, genuine
    approval from ever being applied -- this test would have caught
    that regression directly."""
    from src.shared.media.providers.cloudinary_provider import CloudinaryMediaProvider
    from src.shared.media.config.media_config import MediaConfig

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    public_id = folder_naming.supplier_product_folder(profile.id, product.id) + "/real-sequence"
    product_media_service.register_uploaded_media(
        product.id, profile.id, public_id, "https://x/real-sequence.jpg", "image", "jpg", 600, 600, 35302
    )

    real_provider = CloudinaryMediaProvider(MediaConfig(cloud_name="x", api_key="x", api_secret="x"))

    # Webhook 1 -- the real "upload" notification, arrives first.
    upload_notification = real_provider.parse_scan_result(
        {
            "notification_type": "upload",
            "public_id": public_id,
            "moderation": [{"kind": "perception_point", "status": "pending"}],
        }
    )
    product_media_service.apply_scan_result(upload_notification)

    # Webhook 2 -- the real "moderation" notification, arrives seconds later.
    moderation_notification = real_provider.parse_scan_result(
        {
            "notification_type": "moderation",
            "moderation_status": "approved",
            "moderation_kind": "perception_point",
            "public_id": public_id,
        }
    )
    product_media_service.apply_scan_result(moderation_notification)

    media = ProductMediaRepository.get_by_public_id(public_id)
    assert media.scan_status == MediaScanStatus.APPROVED.value


def test_apply_scan_result_ignores_a_non_scan_notification_without_touching_the_row(
    fake_provider, make_supplier, make_supplier_profile
):
    """The actual bug found during real device testing: Cloudinary's
    own "upload" notification (IGNORED, not a real verdict -- see
    ScanResult's own docstring) must leave the row exactly as it was,
    still PENDING, not misfiled as ERROR."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    public_id = folder_naming.supplier_product_folder(profile.id, product.id) + "/scan-me"
    product_media_service.register_uploaded_media(
        product.id, profile.id, public_id, "https://x/scan-me.jpg", "image", "jpg", 100, 100, 500
    )

    product_media_service.apply_scan_result(ScanResult(public_id=public_id, status="IGNORED", provider="cloudinary"))

    media = ProductMediaRepository.get_by_public_id(public_id)
    assert media.scan_status == MediaScanStatus.PENDING.value
    assert media.scanned_at is None


def test_apply_scan_result_stores_a_large_real_payload_without_crashing(
    fake_provider, make_supplier, make_supplier_profile
):
    """Real bug found during device testing: a genuine Cloudinary
    payload (with its own nested notification_context/triggered_by
    fields) exceeded the old VARCHAR(500) cap and crashed the whole
    webhook handler with a database error. Proves the fix holds
    against a payload at least as large as the real one that broke
    it."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    public_id = folder_naming.supplier_product_folder(profile.id, product.id) + "/scan-me2"
    product_media_service.register_uploaded_media(
        product.id, profile.id, public_id, "https://x/scan-me2.jpg", "image", "jpg", 100, 100, 500
    )
    large_raw_result = "x" * 2000  # comfortably past the old 500-char cap

    product_media_service.apply_scan_result(
        ScanResult(public_id=public_id, status="APPROVED", provider="cloudinary", raw_result=large_raw_result)
    )

    media = ProductMediaRepository.get_by_public_id(public_id)
    assert media.scan_status == MediaScanStatus.APPROVED.value
    assert media.scan_result == large_raw_result


# --- list_approved_media --------------------------------------------------


def test_list_approved_media_excludes_pending_and_rejected(fake_provider, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    approved = ProductMediaRepository.create_pending(
        product.id, "a1", "https://x/approved.jpg", "image", "jpg", 100, 100, 500, 0
    )
    ProductMediaRepository.apply_scan_status(approved, MediaScanStatus.APPROVED.value, "cloudinary", None)
    ProductMediaRepository.create_pending(product.id, "a2", "https://x/pending.jpg", "image", "jpg", 100, 100, 500, 1)
    rejected = ProductMediaRepository.create_pending(
        product.id, "a3", "https://x/rejected.jpg", "image", "jpg", 100, 100, 500, 2
    )
    ProductMediaRepository.apply_scan_status(rejected, MediaScanStatus.REJECTED.value, "cloudinary", None)

    urls = product_media_service.list_approved_media(product.id)

    assert urls == ["https://x/approved.jpg"]


# --- Upload intent integration ---------------------------------------------


def test_request_upload_signature_creates_an_upload_intent(fake_provider, make_supplier, make_supplier_profile):
    from src.shared.media.intents.models import MediaUploadIntentStatus
    from src.shared.media.intents.repositories import MediaUploadIntentRepository

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    signed = product_media_service.request_upload_signature(product.id, profile.id)

    intent = MediaUploadIntentRepository.get_by_public_id(signed.public_id)
    assert intent is not None
    assert intent.status == MediaUploadIntentStatus.ISSUED.value
    assert intent.account_id == profile.id


def test_register_uploaded_media_marks_the_intent_registered(fake_provider, make_supplier, make_supplier_profile):
    from src.shared.media.intents.models import MediaUploadIntentStatus
    from src.shared.media.intents.repositories import MediaUploadIntentRepository

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    signed = product_media_service.request_upload_signature(product.id, profile.id)

    product_media_service.register_uploaded_media(
        product.id, profile.id, signed.public_id, "https://x/real.jpg", "image", "jpg", 800, 600, 50_000
    )

    intent = MediaUploadIntentRepository.get_by_public_id(signed.public_id)
    assert intent.status == MediaUploadIntentStatus.REGISTERED.value
    assert intent.registered_at is not None


def test_register_uploaded_media_cancels_the_intent_when_oversized_and_rejected(
    fake_provider, make_supplier, make_supplier_profile
):
    """The oversized-file rejection path deletes the asset itself
    immediately -- the intent should be resolved right away too, not
    left ISSUED for the sweep to rediscover up to an hour later."""
    from src.shared.media.intents.models import MediaUploadIntentStatus
    from src.shared.media.intents.repositories import MediaUploadIntentRepository

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    signed = product_media_service.request_upload_signature(product.id, profile.id)
    oversized_bytes = 100 * 1024 * 1024

    with pytest.raises(PhotoLimitExceededError):
        product_media_service.register_uploaded_media(
            product.id, profile.id, signed.public_id, "https://x/big.jpg", "image", "jpg", 100, 100, oversized_bytes
        )

    intent = MediaUploadIntentRepository.get_by_public_id(signed.public_id)
    assert intent.status == MediaUploadIntentStatus.CANCELLED.value


def test_upload_and_register_from_bytes_never_creates_an_intent(fake_provider, make_supplier, make_supplier_profile):
    """Bulk import's own path uploads and registers in one atomic
    step, never through the signed-upload flow -- no intent should
    exist for it at all."""
    from src.shared.media.intents.repositories import MediaUploadIntentRepository

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    media = product_media_service.upload_and_register_from_bytes(product.id, profile.id, b"fake image bytes")

    intent = MediaUploadIntentRepository.get_by_public_id(media.cloudinary_public_id)
    assert intent is None
