"""
Inventory repository + service tests. Same split as products' own
test_product_service.py: repository tests confirm the SQL, service
tests confirm the actual business rules (status computation, the
negative-stock guard, lazy record creation, ownership).
"""
from __future__ import annotations

import pytest

from src.domains.supplier.inventory.models.inventory import LowStockAlertChannel
from src.domains.supplier.inventory.repositories.inventory_repository import (
    InventoryRepository,
    InventorySettingsRepository,
)
from src.domains.supplier.inventory.services import inventory_service
from src.domains.supplier.inventory.services.errors import (
    InsufficientStockError,
    InventoryValidationError,
    ProductNotFoundError,
)
from src.domains.supplier.products.models.product import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_repository import ProductRepository


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


# --- Lazy creation -----------------------------------------------------


def test_get_or_create_for_product_seeds_zero_quantity(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    inventory = InventoryRepository.get_or_create_for_product(product.id, profile.id)

    assert inventory.quantity_on_hand == 0
    assert inventory.quantity_reserved == 0
    assert inventory.low_stock_threshold == 5  # default


def test_get_or_create_for_product_uses_supplier_default_threshold(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    InventorySettingsRepository.get_or_create_for_supplier(profile.id)
    settings = InventorySettingsRepository.update(
        InventorySettingsRepository.get_or_create_for_supplier(profile.id), default_low_stock_threshold=15
    )
    product = _make_product(profile.id)

    inventory = InventoryRepository.get_or_create_for_product(product.id, profile.id)

    assert inventory.low_stock_threshold == 15
    assert settings.default_low_stock_threshold == 15


def test_get_or_create_for_product_is_idempotent(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    first = InventoryRepository.get_or_create_for_product(product.id, profile.id)
    InventoryRepository.adjust_quantity(first, 50)
    second = InventoryRepository.get_or_create_for_product(product.id, profile.id)

    assert first.id == second.id
    assert second.quantity_on_hand == 50


# --- Status computation --------------------------------------------------


def test_status_is_in_stock_above_threshold(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    inventory_service.adjust_stock(product.id, profile.id, 50, "STOCK_RECEIVED")

    item = inventory_service.get_inventory_item(product.id, profile.id)

    assert item["status"] == "IN_STOCK"
    assert item["available_quantity"] == 50


def test_status_is_low_stock_at_or_below_threshold(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    inventory_service.adjust_stock(product.id, profile.id, 5, "STOCK_RECEIVED")  # default threshold is 5

    item = inventory_service.get_inventory_item(product.id, profile.id)

    assert item["status"] == "LOW_STOCK"


def test_status_is_out_of_stock_at_zero(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    item = inventory_service.get_inventory_item(product.id, profile.id)

    assert item["status"] == "OUT_OF_STOCK"
    assert item["available_quantity"] == 0


def test_out_of_stock_wins_even_if_threshold_is_also_zero(make_supplier, make_supplier_profile):
    """Zero-or-below is OUT_OF_STOCK even if the threshold is also 0 --
    a threshold of 0 doesn't mean 'never low stock'. Same order-of-
    checks the frontend's own algorithm enforces."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    inventory_service.set_low_stock_threshold(product.id, profile.id, 0)

    item = inventory_service.get_inventory_item(product.id, profile.id)

    assert item["status"] == "OUT_OF_STOCK"


# --- Adjust stock --------------------------------------------------------


def test_adjust_stock_positive_delta_increases_quantity(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    item = inventory_service.adjust_stock(product.id, profile.id, 20, "STOCK_RECEIVED")

    assert item["inventory"].quantity_on_hand == 20


def test_adjust_stock_negative_delta_decreases_quantity(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    inventory_service.adjust_stock(product.id, profile.id, 20, "STOCK_RECEIVED")

    item = inventory_service.adjust_stock(product.id, profile.id, -5, "STOCK_SOLD")

    assert item["inventory"].quantity_on_hand == 15


def test_adjust_stock_rejects_taking_quantity_below_zero(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    inventory_service.adjust_stock(product.id, profile.id, 10, "STOCK_RECEIVED")

    with pytest.raises(InsufficientStockError):
        inventory_service.adjust_stock(product.id, profile.id, -11, "STOCK_SOLD")

    # Rejected adjustment must not have partially applied.
    item = inventory_service.get_inventory_item(product.id, profile.id)
    assert item["inventory"].quantity_on_hand == 10


def test_adjust_stock_raises_not_found_for_other_suppliers_product(make_supplier, make_supplier_profile):
    owner = make_supplier("inv-owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Inv Owner Co")
    other = make_supplier("inv-other@example.com")
    other_profile = make_supplier_profile(other, business_name="Inv Other Co")
    product = _make_product(owner_profile.id)

    with pytest.raises(ProductNotFoundError):
        inventory_service.adjust_stock(product.id, other_profile.id, 10, "STOCK_RECEIVED")


# --- Threshold -------------------------------------------------------------


def test_set_low_stock_threshold_persists(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    item = inventory_service.set_low_stock_threshold(product.id, profile.id, 12)

    assert item["inventory"].low_stock_threshold == 12


def test_set_low_stock_threshold_rejects_negative(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    with pytest.raises(InventoryValidationError):
        inventory_service.set_low_stock_threshold(product.id, profile.id, -1)


# --- Settings --------------------------------------------------------------


def test_update_settings_partial_update_preserves_other_field(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    inventory_service.update_settings(profile.id, default_low_stock_threshold=20)

    settings = inventory_service.update_settings(profile.id, low_stock_alert_channel="EMAIL")

    assert settings.default_low_stock_threshold == 20
    assert settings.low_stock_alert_channel == LowStockAlertChannel.EMAIL


def test_update_settings_rejects_negative_threshold(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    with pytest.raises(InventoryValidationError):
        inventory_service.update_settings(profile.id, default_low_stock_threshold=-5)


# --- List / summary ----------------------------------------------------


def test_get_inventory_list_filters_by_status(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    in_stock = _make_product(profile.id, name="In Stock Item")
    out_of_stock = _make_product(profile.id, name="Out Item")
    inventory_service.adjust_stock(in_stock.id, profile.id, 50, "STOCK_RECEIVED")

    results = inventory_service.get_inventory_list(profile.id, status_filter="OUT_OF_STOCK")

    names = {item["product"].name for item in results}
    assert names == {"Out Item"}


def test_get_inventory_summary_counts_each_status(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A")
    p2 = _make_product(profile.id, name="B")
    p3 = _make_product(profile.id, name="C")
    inventory_service.adjust_stock(p1.id, profile.id, 50, "STOCK_RECEIVED")  # IN_STOCK
    inventory_service.adjust_stock(p2.id, profile.id, 3, "STOCK_RECEIVED")  # LOW_STOCK (threshold 5)
    # p3 stays at 0 -- OUT_OF_STOCK

    summary = inventory_service.get_inventory_summary(profile.id)

    assert summary["total_products"] == 3
    assert summary["in_stock_count"] == 1
    assert summary["low_stock_count"] == 1
    assert summary["out_of_stock_count"] == 1
