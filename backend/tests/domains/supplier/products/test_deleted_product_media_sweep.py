"""
Tests for products/jobs/deleted_product_media_sweep.py -- the deferred
Cloudinary cleanup for soft-deleted products' real photos. FakeMediaProvider
duplicated here rather than imported, same reasoning as
test_media_api.py's own docstring.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domains.supplier.products.jobs import deleted_product_media_sweep
from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_media_repository import ProductMediaRepository
from src.domains.supplier.products.services import product_media_service, product_service
from src.shared.media.providers.provider import MediaProvider, ScanResult, SignedUpload, UploadedAsset


class FakeMediaProvider(MediaProvider):
    def __init__(self):
        # Each call's FULL batch, preserved separately -- this is what
        # actually proves batching (one call handling many photos),
        # not just "everything got deleted eventually".
        self.delete_assets_calls: list[list[str]] = []
        self.delete_folder_calls: list[str] = []

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
            moderation="",
            asset_folder=asset_folder,
        )

    def verify_webhook_signature(self, raw_body: str, timestamp: str, signature: str) -> bool:
        return True

    def parse_scan_result(self, payload: dict) -> ScanResult:
        return ScanResult(public_id=payload.get("public_id", ""), status="APPROVED", provider="fake")

    def delete_asset(self, public_id: str) -> None:
        self.delete_assets_calls.append([public_id])

    def delete_assets(self, public_ids: list) -> None:
        self.delete_assets_calls.append(list(public_ids))

    def delete_folder(self, folder_path: str) -> None:
        self.delete_folder_calls.append(folder_path)

    def is_moderation_enabled(self) -> bool:
        return False

    @property
    def all_deleted_public_ids(self) -> list:
        return [pid for batch in self.delete_assets_calls for pid in batch]


@pytest.fixture()
def fake_provider(monkeypatch):
    provider = FakeMediaProvider()
    monkeypatch.setattr(product_media_service, "get_media_provider", lambda: provider)
    monkeypatch.setattr(deleted_product_media_sweep, "get_media_provider", lambda: provider)
    return provider


@pytest.fixture(autouse=True)
def _real_grace_period():
    """Every test in this file exercises the REAL 7-day grace period
    (via backdating), never the testing override -- restores whatever
    was there before, regardless of what a test sets."""
    original = deleted_product_media_sweep.DELETE_GRACE_PERIOD
    deleted_product_media_sweep.DELETE_GRACE_PERIOD = timedelta(days=7)
    yield
    deleted_product_media_sweep.DELETE_GRACE_PERIOD = original


def _make_product(supplier_profile_id, name="Test Product"):
    return product_service.create_product(
        supplier_profile_id=supplier_profile_id,
        name=name,
        category=ProductCategory.OTHER,
        price_cents=1000,
        selling_unit=ProductUnit.EACH,
    )


def _backdate_product_delete(product_id, days_ago: int) -> None:
    from src.extensions import db
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer

    row = db.session.get(SupplierOffer, product_id)
    row.deleted_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    db.session.commit()


def test_sweep_cleans_up_media_for_a_product_deleted_past_the_grace_period(
    fake_provider, make_supplier, make_supplier_profile
):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    media = product_media_service.upload_and_register_from_bytes(product.id, profile.id, b"fake bytes")
    product_service.delete_product(product.id, profile.id)
    _backdate_product_delete(product.id, days_ago=8)  # past the real 7-day grace period

    result = deleted_product_media_sweep.run()

    assert result.success is True
    assert result.count == 1
    assert media.cloudinary_public_id in fake_provider.all_deleted_public_ids

    cleaned_media = ProductMediaRepository.get_by_id_and_product(media.id, product.id)
    assert cleaned_media is None  # correctly filtered out now it's marked deleted too


def test_sweep_leaves_media_for_a_recently_deleted_product_alone(fake_provider, make_supplier, make_supplier_profile):
    """Still within the grace period -- nothing should be touched yet,
    same "give suppliers real room to undo a mistake" reasoning as the
    module's own docstring."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    product_media_service.upload_and_register_from_bytes(product.id, profile.id, b"fake bytes")
    product_service.delete_product(product.id, profile.id)
    _backdate_product_delete(product.id, days_ago=1)  # well within the 7-day grace period

    result = deleted_product_media_sweep.run()

    assert result.count == 0
    assert fake_provider.delete_assets_calls == []


def test_sweep_leaves_media_for_active_products_alone(fake_provider, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    product_media_service.upload_and_register_from_bytes(product.id, profile.id, b"fake bytes")
    # SupplierOffer is never deleted at all.

    result = deleted_product_media_sweep.run()

    assert result.count == 0
    assert fake_provider.delete_assets_calls == []


def test_sweep_continues_past_a_batch_delete_failure(fake_provider, make_supplier, make_supplier_profile, monkeypatch):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product1 = _make_product(profile.id, name="P1")
    media1 = product_media_service.upload_and_register_from_bytes(product1.id, profile.id, b"bytes1")
    product2 = _make_product(profile.id, name="P2")
    media2 = product_media_service.upload_and_register_from_bytes(product2.id, profile.id, b"bytes2")
    product_service.delete_product(product1.id, profile.id)
    product_service.delete_product(product2.id, profile.id)
    _backdate_product_delete(product1.id, days_ago=8)
    _backdate_product_delete(product2.id, days_ago=8)

    call_count = {"n": 0}
    original_delete_assets = fake_provider.delete_assets

    def _flaky_delete_assets(public_ids):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("simulated Cloudinary failure")
        original_delete_assets(public_ids)

    monkeypatch.setattr(fake_provider, "delete_assets", _flaky_delete_assets)

    result = deleted_product_media_sweep.run()

    # Both marked cleaned up regardless of which product's batch call
    # failed -- same resilience already proven for the orphan upload
    # sweep, just at the batch level instead of the single-item level.
    assert result.count == 2
    assert ProductMediaRepository.get_by_id_and_product(media1.id, product1.id) is None
    assert ProductMediaRepository.get_by_id_and_product(media2.id, product2.id) is None


def test_sweep_continues_past_a_folder_delete_failure(fake_provider, make_supplier, make_supplier_profile, monkeypatch):
    """Folder cleanup is purely cosmetic (see the sweep's own
    docstring) -- it failing must never block the real, meaningful
    part (the assets themselves getting deleted and the media rows
    getting marked cleaned up)."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    media = product_media_service.upload_and_register_from_bytes(product.id, profile.id, b"bytes")
    product_service.delete_product(product.id, profile.id)
    _backdate_product_delete(product.id, days_ago=8)

    def _failing_delete_folder(folder_path):
        raise RuntimeError("simulated folder-not-empty error")

    monkeypatch.setattr(fake_provider, "delete_folder", _failing_delete_folder)

    result = deleted_product_media_sweep.run()

    assert result.count == 1
    assert media.cloudinary_public_id in fake_provider.all_deleted_public_ids
    assert ProductMediaRepository.get_by_id_and_product(media.id, product.id) is None


def test_a_products_photos_are_batched_into_one_call_not_one_per_photo(
    fake_provider, make_supplier, make_supplier_profile
):
    """THE REAL FIX -- a product with several photos must produce ONE
    real delete_assets call covering all of them, not one call per
    photo. This is the entire point of the batching work: fewer real
    network round trips per product, regardless of how many photos it
    had."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    media_items = [
        product_media_service.upload_and_register_from_bytes(product.id, profile.id, f"bytes{i}".encode())
        for i in range(2)  # Free tier's own real cap -- see products/tiers/free.py
    ]
    product_service.delete_product(product.id, profile.id)
    _backdate_product_delete(product.id, days_ago=8)

    result = deleted_product_media_sweep.run()

    assert result.count == 2
    assert len(fake_provider.delete_assets_calls) == 1  # ONE call, not two
    assert sorted(fake_provider.delete_assets_calls[0]) == sorted(m.cloudinary_public_id for m in media_items)


def test_the_products_own_folder_is_deleted_once_its_photos_are_gone(
    fake_provider, make_supplier, make_supplier_profile
):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    media = product_media_service.upload_and_register_from_bytes(product.id, profile.id, b"bytes")
    product_service.delete_product(product.id, profile.id)
    _backdate_product_delete(product.id, days_ago=8)

    deleted_product_media_sweep.run()

    expected_folder = media.cloudinary_public_id.rsplit("/", 1)[0]
    assert fake_provider.delete_folder_calls == [expected_folder]


def test_two_different_products_get_two_separate_batches_and_folders(
    fake_provider, make_supplier, make_supplier_profile
):
    """Confirms grouping is genuinely PER PRODUCT -- two products'
    photos must never end up merged into the same batch call or
    folder delete, even though both are cleaned up in the same run."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product1 = _make_product(profile.id, name="P1")
    media1 = product_media_service.upload_and_register_from_bytes(product1.id, profile.id, b"bytes1")
    product2 = _make_product(profile.id, name="P2")
    media2 = product_media_service.upload_and_register_from_bytes(product2.id, profile.id, b"bytes2")
    product_service.delete_product(product1.id, profile.id)
    product_service.delete_product(product2.id, profile.id)
    _backdate_product_delete(product1.id, days_ago=8)
    _backdate_product_delete(product2.id, days_ago=8)

    result = deleted_product_media_sweep.run()

    assert result.count == 2
    assert len(fake_provider.delete_assets_calls) == 2
    assert len(fake_provider.delete_folder_calls) == 2
    assert media1.cloudinary_public_id in fake_provider.delete_assets_calls[0] + fake_provider.delete_assets_calls[1]
    assert media2.cloudinary_public_id in fake_provider.delete_assets_calls[0] + fake_provider.delete_assets_calls[1]


def test_per_run_cap_defers_the_rest_to_a_later_run(fake_provider, make_supplier, make_supplier_profile, monkeypatch):
    """THE REAL "PROTECT A SINGLE RUN" SAFEGUARD -- with the cap set
    to 2, a backlog of 3 eligible products must only see 2 of them
    processed in this run; the third is left completely untouched,
    genuinely deferred rather than silently dropped, and picked up
    correctly the next time run() is called."""
    monkeypatch.setattr(deleted_product_media_sweep, "MAX_PRODUCTS_PER_RUN", 2)

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    products_and_media = []
    for i in range(3):
        product = _make_product(profile.id, name=f"P{i}")
        media = product_media_service.upload_and_register_from_bytes(product.id, profile.id, f"bytes{i}".encode())
        product_service.delete_product(product.id, profile.id)
        # Oldest-deleted-first ordering matters here -- backdating by
        # DIFFERENT amounts so which 2 of the 3 get processed first is
        # deterministic, not a coin flip.
        _backdate_product_delete(product.id, days_ago=10 - i)
        products_and_media.append((product, media))

    first_run = deleted_product_media_sweep.run()

    assert first_run.count == 2  # capped, not all 3
    oldest_two = products_and_media[:2]
    still_pending = products_and_media[2]
    for product, media in oldest_two:
        assert ProductMediaRepository.get_by_id_and_product(media.id, product.id) is None
    still_pending_product, still_pending_media = still_pending
    assert ProductMediaRepository.get_by_id_and_product(still_pending_media.id, still_pending_product.id) is not None

    # The deferred one genuinely gets picked up next time, nothing lost.
    second_run = deleted_product_media_sweep.run()
    assert second_run.count == 1
    assert (
        ProductMediaRepository.get_by_id_and_product(still_pending_media.id, still_pending_product.id) is None
    )
