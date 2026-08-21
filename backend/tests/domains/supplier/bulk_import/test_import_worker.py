"""
import_worker tests -- the core proof that Bulk Import actually
creates real Products via the SAME product_service every other path
uses, seeds real Inventory quantities, and matches/uploads real
images. Uses a FakeMediaProvider (same pattern as test_media_api.py)
since this environment has no network access to Cloudinary -- see that
file's own docstring for why that's the right test double here, not a
gap.
"""
from __future__ import annotations

import zipfile

import pytest

from src.domains.supplier.bulk_import.models.import_job import ImportJobStatus
from src.domains.supplier.bulk_import.repositories.import_job_repository import ImportJobRepository
from src.domains.supplier.bulk_import.workers.import_worker import run_import
from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.products.services import product_media_service
from src.shared.media.providers.provider import MediaProvider, ScanResult, SignedUpload, UploadedAsset


class FakeMediaProvider(MediaProvider):
    def __init__(self):
        self.uploaded: list = []

    def generate_signed_upload(self, public_id: str, max_dimension_px: int = 1600) -> SignedUpload:
        raise NotImplementedError("bulk import never uses the signed-client-upload path")

    def upload_asset(self, public_id: str, file_bytes: bytes, max_dimension_px: int = 1600, resource_type: str = "image") -> UploadedAsset:
        self.uploaded.append(public_id)
        return UploadedAsset(
            public_id=public_id,
            secure_url=f"https://res.cloudinary.com/test/{public_id}.jpg",
            resource_type=resource_type,
            format="jpg",
            width=800,
            height=600,
            bytes=len(file_bytes),
        )

    def verify_webhook_signature(self, raw_body: str, timestamp: str, signature: str) -> bool:
        return True

    def parse_scan_result(self, payload: dict) -> ScanResult:
        return ScanResult(public_id=payload.get("public_id", ""), status="APPROVED", provider="fake")

    def delete_asset(self, public_id: str) -> None:
        pass


@pytest.fixture()
def fake_provider(monkeypatch):
    provider = FakeMediaProvider()
    monkeypatch.setattr(product_media_service, "get_media_provider", lambda: provider)
    return provider


def _make_zip_bytes(tmp_path, entries: dict) -> bytes:
    path = str(tmp_path / "images.zip")
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    with open(path, "rb") as f:
        return f.read()


def _make_job(profile_id, filename="import.csv", has_zip=False):
    return ImportJobRepository.create(profile_id, filename, has_zip)


class TestBasicImport:
    def test_creates_real_products_from_valid_rows(self, fake_provider, make_supplier, make_supplier_profile):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id)
        csv_bytes = (
            b"name,category,price,unit,quantity\n"
            b"Coca-Cola 500ml,Beverages,12.00,Each,47\n"
            b"Bread,Bakery,19.99,Each,0\n"
        )

        run_import(job.id, profile.id, "import.csv", csv_bytes, None, None)

        products = ProductRepository.list_for_supplier(profile.id)
        names = {p.name for p in products}
        assert names == {"Coca-Cola 500ml", "Bread"}

    def test_seeds_real_inventory_quantity(self, fake_provider, make_supplier, make_supplier_profile):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id)
        csv_bytes = b"name,category,price,unit,quantity\nCoca-Cola 500ml,Beverages,12.00,Each,47\n"

        run_import(job.id, profile.id, "import.csv", csv_bytes, None, None)

        product = ProductRepository.list_for_supplier(profile.id)[0]
        inventory = InventoryRepository.get_by_product_id(product.id)
        assert inventory.quantity_on_hand == 47

    def test_zero_quantity_creates_product_without_inventory_call(
        self, fake_provider, make_supplier, make_supplier_profile
    ):
        """A product with quantity=0 should still exist -- Inventory's
        own lazy get_or_create means it correctly reads 0 even though
        adjust_stock was never called for this row."""
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id)
        csv_bytes = b"name,category,price,unit\nBread,Bakery,19.99,Each\n"

        run_import(job.id, profile.id, "import.csv", csv_bytes, None, None)

        product = ProductRepository.list_for_supplier(profile.id)[0]
        inventory = InventoryRepository.get_or_create_for_product(product.id, profile.id)
        assert inventory.quantity_on_hand == 0

    def test_job_counts_and_status_are_updated_correctly(self, fake_provider, make_supplier, make_supplier_profile):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id)
        csv_bytes = (
            b"name,category,price,unit\n" b"Good One,Beverages,12.00,Each\n" b"Bad Row,NotARealCategory,12.00,Each\n"
        )

        run_import(job.id, profile.id, "import.csv", csv_bytes, None, None)

        refreshed = ImportJobRepository.get_by_id_and_supplier(job.id, profile.id)
        assert refreshed.status == ImportJobStatus.COMPLETED
        assert refreshed.total_rows == 2
        assert refreshed.valid_rows == 1
        assert refreshed.error_rows == 1
        assert refreshed.created_rows == 1

    def test_row_errors_are_recorded_with_row_number(self, fake_provider, make_supplier, make_supplier_profile):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id)
        csv_bytes = b"name,category,price,unit\nBad Row,NotARealCategory,12.00,Each\n"

        run_import(job.id, profile.id, "import.csv", csv_bytes, None, None)

        errors = ImportJobRepository.list_errors(job.id)
        assert len(errors) == 1
        assert errors[0].row_number == 2  # header is row 1
        assert errors[0].field == "category"


class TestImageHandling:
    def test_matched_image_gets_uploaded_and_registered(
        self, fake_provider, make_supplier, make_supplier_profile, tmp_path
    ):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id, has_zip=True)
        csv_bytes = b"name,category,price,unit,image_1\nCoca-Cola 500ml,Beverages,12.00,Each,coke500.jpg\n"
        zip_bytes = _make_zip_bytes(tmp_path, {"coke500.jpg": b"real jpeg data"})

        run_import(job.id, profile.id, "import.csv", csv_bytes, "images.zip", zip_bytes)

        assert len(fake_provider.uploaded) == 1

    def test_row_referencing_missing_image_becomes_a_hard_error(
        self, fake_provider, make_supplier, make_supplier_profile, tmp_path
    ):
        """Matches the frontend's own applyImageManifest exactly -- a
        row naming an image that isn't actually in the ZIP fails the
        WHOLE row, not just skips the image."""
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id, has_zip=True)
        csv_bytes = b"name,category,price,unit,image_1\nCoca-Cola 500ml,Beverages,12.00,Each,doesnotexist.jpg\n"
        zip_bytes = _make_zip_bytes(tmp_path, {"unrelated.jpg": b"data"})

        run_import(job.id, profile.id, "import.csv", csv_bytes, "images.zip", zip_bytes)

        products = ProductRepository.list_for_supplier(profile.id)
        assert len(products) == 0  # the row failed entirely, no product created

        errors = ImportJobRepository.list_errors(job.id)
        assert any("not found in ZIP" in e.message for e in errors)

    def test_image_reference_without_any_zip_uploaded_is_a_hard_error(
        self, fake_provider, make_supplier, make_supplier_profile
    ):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id, has_zip=False)
        csv_bytes = b"name,category,price,unit,image_1\nCoca-Cola 500ml,Beverages,12.00,Each,coke500.jpg\n"

        run_import(job.id, profile.id, "import.csv", csv_bytes, None, None)

        products = ProductRepository.list_for_supplier(profile.id)
        assert len(products) == 0
        errors = ImportJobRepository.list_errors(job.id)
        assert any("no ZIP was uploaded" in e.message for e in errors)

    def test_case_difference_between_csv_and_zip_filename_is_resolved_automatically(
        self, fake_provider, make_supplier, make_supplier_profile, tmp_path
    ):
        """Found during real device testing: the CSV said "Coke500.jpg",
        the ZIP actually contained "coke500.jpg" -- case can never be
        genuinely ambiguous, so this must succeed, not error."""
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id, has_zip=True)
        csv_bytes = b"name,category,price,unit,image_1\nCoca-Cola 500ml,Beverages,12.00,Each,Coke500.JPG\n"
        zip_bytes = _make_zip_bytes(tmp_path, {"coke500.jpg": b"real jpeg data"})

        run_import(job.id, profile.id, "import.csv", csv_bytes, "images.zip", zip_bytes)

        products = ProductRepository.list_for_supplier(profile.id)
        assert len(products) == 1  # the row succeeded despite the case mismatch
        assert len(fake_provider.uploaded) == 1
        errors = ImportJobRepository.list_errors(job.id)
        assert errors == []

    def test_genuine_typo_in_image_filename_gets_a_did_you_mean_suggestion(
        self, fake_provider, make_supplier, make_supplier_profile, tmp_path
    ):
        """Unlike case, a real typo is genuinely ambiguous -- must
        still fail the row, but the error should point at the likely
        real filename rather than leave the supplier guessing."""
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id, has_zip=True)
        csv_bytes = b"name,category,price,unit,image_1\nCoca-Cola 500ml,Beverages,12.00,Each,coke50.jpg\n"
        zip_bytes = _make_zip_bytes(tmp_path, {"coke500.jpg": b"real jpeg data"})

        run_import(job.id, profile.id, "import.csv", csv_bytes, "images.zip", zip_bytes)

        products = ProductRepository.list_for_supplier(profile.id)
        assert len(products) == 0  # still a hard error, never auto-corrected

        errors = ImportJobRepository.list_errors(job.id)
        assert any('Did you mean "coke500.jpg"?' in e.message for e in errors)

    def test_wildly_wrong_filename_gets_no_suggestion_rather_than_a_bad_guess(
        self, fake_provider, make_supplier, make_supplier_profile, tmp_path
    ):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id, has_zip=True)
        csv_bytes = b"name,category,price,unit,image_1\nCoca-Cola 500ml,Beverages,12.00,Each,zzzzzzzzzz.jpg\n"
        zip_bytes = _make_zip_bytes(tmp_path, {"coke500.jpg": b"real jpeg data"})

        run_import(job.id, profile.id, "import.csv", csv_bytes, "images.zip", zip_bytes)

        errors = ImportJobRepository.list_errors(job.id)
        assert len(errors) == 1
        assert "Did you mean" not in errors[0].message


class TestUnsafeFileHandling:
    def test_unsafe_zip_fails_the_whole_job_not_partial_processing(
        self, fake_provider, make_supplier, make_supplier_profile, tmp_path
    ):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id, has_zip=True)
        csv_bytes = b"name,category,price,unit\nCoca-Cola 500ml,Beverages,12.00,Each\n"
        # A path-traversal zip -- must fail the whole job before any
        # product is created.
        path = str(tmp_path / "evil.zip")
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr("../../evil.jpg", b"data")
        with open(path, "rb") as f:
            zip_bytes = f.read()

        run_import(job.id, profile.id, "import.csv", csv_bytes, "evil.zip", zip_bytes)

        refreshed = ImportJobRepository.get_by_id_and_supplier(job.id, profile.id)
        assert refreshed.status == ImportJobStatus.FAILED
        assert ProductRepository.list_for_supplier(profile.id) == []


class TestTierGatedLimits:
    """FREE tier (the only tier get_current_tier ever resolves to
    today): bulk_max_rows_per_job=500, bulk_max_images_per_job=15 --
    see products/tiers/free.py's own numbers."""

    def test_row_count_exceeding_tier_limit_fails_whole_job(
        self, fake_provider, make_supplier, make_supplier_profile
    ):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id)
        lines = ["name,category,price,unit"] + [f"Product {i},Other,1.00,Each" for i in range(501)]
        csv_bytes = ("\n".join(lines)).encode("utf-8")

        run_import(job.id, profile.id, "import.csv", csv_bytes, None, None)

        refreshed = ImportJobRepository.get_by_id_and_supplier(job.id, profile.id)
        assert refreshed.status == ImportJobStatus.FAILED
        assert ProductRepository.list_for_supplier(profile.id) == []
        errors = ImportJobRepository.list_errors(job.id)
        assert any("your plan allows up to" in e.message.lower() for e in errors)

    def test_job_wide_image_cap_stops_further_uploads_but_keeps_creating_products(
        self, fake_provider, make_supplier, make_supplier_profile, tmp_path
    ):
        """The job-wide image ceiling (15) is lower than the row count
        (20) -- every product should still get created; only images
        beyond the 15th should be skipped, with ONE job-level error,
        not twenty individual ones."""
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)
        job = _make_job(profile.id, has_zip=True)

        lines = ["name,category,price,unit,image_1"]
        images = {}
        for i in range(20):
            filename = f"img{i}.jpg"
            lines.append(f"Product {i},Other,1.00,Each,{filename}")
            images[filename] = f"data-{i}".encode()
        csv_bytes = ("\n".join(lines)).encode("utf-8")
        zip_bytes = _make_zip_bytes(tmp_path, images)

        run_import(job.id, profile.id, "import.csv", csv_bytes, "images.zip", zip_bytes)

        products = ProductRepository.list_for_supplier(profile.id)
        assert len(products) == 20  # every row still creates a product

        assert len(fake_provider.uploaded) == 15  # capped at the tier's own ceiling

        refreshed = ImportJobRepository.get_by_id_and_supplier(job.id, profile.id)
        assert refreshed.images_matched == 15

        errors = ImportJobRepository.list_errors(job.id)
        cap_errors = [e for e in errors if "allows up to 15 images per import" in e.message]
        assert len(cap_errors) == 1  # ONE error, not one per skipped image
