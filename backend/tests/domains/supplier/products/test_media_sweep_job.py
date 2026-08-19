"""
Stuck-media sweep job tests.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.domains.supplier.products.models.product import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_media_repository import ProductMediaRepository
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.extensions import db
from src.shared.media.jobs import stuck_media_sweep
from src.shared.media.mixins import MediaScanStatus


def _make_product(profile_id, **overrides):
    defaults = dict(
        supplier_profile_id=profile_id,
        name="Coca-Cola 500ml",
        category=ProductCategory.BEVERAGES,
        price_cents=1200,
        selling_unit=ProductUnit.EACH,
    )
    defaults.update(overrides)
    return ProductRepository.create(**defaults)


def test_sweep_marks_old_pending_media_as_error(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    stuck = ProductMediaRepository.create_pending(
        product.id, "stuck1", "https://x/stuck1.jpg", "image", "jpg", 100, 100, 500, 0
    )
    # Backdate created_at past the sweep's own timeout.
    stuck.created_at = datetime.now(timezone.utc) - timedelta(minutes=60)
    db.session.commit()

    result = stuck_media_sweep.run()

    assert result.success is True
    assert result.count == 1
    refreshed = ProductMediaRepository.get_by_public_id("stuck1")
    assert refreshed.scan_status == MediaScanStatus.ERROR.value


def test_sweep_leaves_recent_pending_media_alone(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    ProductMediaRepository.create_pending(
        product.id, "recent1", "https://x/recent1.jpg", "image", "jpg", 100, 100, 500, 0
    )

    result = stuck_media_sweep.run()

    assert result.count == 0
    still_pending = ProductMediaRepository.get_by_public_id("recent1")
    assert still_pending.scan_status == MediaScanStatus.PENDING.value


def test_sweep_leaves_already_terminal_media_alone(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    approved = ProductMediaRepository.create_pending(
        product.id, "old-approved", "https://x/old.jpg", "image", "jpg", 100, 100, 500, 0
    )
    ProductMediaRepository.apply_scan_status(approved, MediaScanStatus.APPROVED.value, "cloudinary", None)
    approved.created_at = datetime.now(timezone.utc) - timedelta(minutes=60)
    db.session.commit()

    result = stuck_media_sweep.run()

    assert result.count == 0
    refreshed = ProductMediaRepository.get_by_public_id("old-approved")
    assert refreshed.scan_status == MediaScanStatus.APPROVED.value
