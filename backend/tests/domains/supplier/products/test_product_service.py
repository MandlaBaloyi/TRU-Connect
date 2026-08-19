"""
Products repository + service tests. Service tests are the ones that
actually matter for correctness (validation, bulk math, ownership) --
repository tests here are thin, just confirming the SQL does what it
says, matching the split every other domain draws between the two
layers.
"""
from __future__ import annotations

import pytest

from src.domains.supplier.products.models.product import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.products.services import product_service
from src.domains.supplier.products.services.errors import ProductNotFoundError, ProductValidationError


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


# --- Repository ------------------------------------------------------------


def test_repository_create_persists_full_fields(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    product = _make_product(profile.id, unit_quantity=24, unit_measure=ProductUnit.BOTTLE)

    assert product.name == "Coca-Cola 500ml"
    assert product.category == ProductCategory.BEVERAGES
    assert product.price_cents == 1200
    assert product.selling_unit == ProductUnit.EACH
    assert product.unit_quantity == 24
    assert product.unit_measure == ProductUnit.BOTTLE
    assert product.is_archived is False


def test_get_by_id_and_supplier_excludes_other_suppliers_products(make_supplier, make_supplier_profile):
    owner = make_supplier("owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Owner Co")
    other = make_supplier("other@example.com")
    other_profile = make_supplier_profile(other, business_name="Other Co")

    product = _make_product(owner_profile.id)

    assert ProductRepository.get_by_id_and_supplier(product.id, owner_profile.id) is not None
    assert ProductRepository.get_by_id_and_supplier(product.id, other_profile.id) is None


def test_list_for_supplier_excludes_archived_by_default(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    active = _make_product(profile.id, name="Active Product")
    archived = _make_product(profile.id, name="Archived Product")
    ProductRepository.archive(archived)

    results = ProductRepository.list_for_supplier(profile.id)

    names = {p.name for p in results}
    assert names == {"Active Product"}
    assert active.id in [p.id for p in results]


def test_list_for_supplier_search_is_substring_not_prefix(make_supplier, make_supplier_profile):
    """Deliberately different from the public supplier-search endpoint
    (prefix-only) -- see the repository's own docstring."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    _make_product(profile.id, name="Coca-Cola 500ml")
    _make_product(profile.id, name="Fanta Orange 500ml")

    results = ProductRepository.list_for_supplier(profile.id, search_term="500ml")

    assert len(results) == 2


# --- Service: validation ----------------------------------------------------


def test_create_product_rejects_blank_name(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    with pytest.raises(ProductValidationError) as exc_info:
        product_service.create_product(profile.id, "   ", ProductCategory.OTHER, 100, ProductUnit.EACH)

    assert "Product name is required." in exc_info.value.errors


def test_create_product_rejects_negative_price(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    with pytest.raises(ProductValidationError) as exc_info:
        product_service.create_product(profile.id, "Bread", ProductCategory.BAKERY, -100, ProductUnit.EACH)

    assert "Price must be zero or a positive amount." in exc_info.value.errors


def test_create_product_rejects_unrealistic_price(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    with pytest.raises(ProductValidationError) as exc_info:
        product_service.create_product(
            profile.id, "Bread", ProductCategory.BAKERY, 200_000_000, ProductUnit.EACH
        )

    assert any("unrealistically large" in e for e in exc_info.value.errors)


def test_create_product_strips_whitespace_from_name(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    product = product_service.create_product(profile.id, "  Bread  ", ProductCategory.BAKERY, 100, ProductUnit.EACH)

    assert product.name == "Bread"


def test_update_product_raises_not_found_for_other_suppliers_product(make_supplier, make_supplier_profile):
    owner = make_supplier("owner2@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Owner Co 2")
    other = make_supplier("other2@example.com")
    other_profile = make_supplier_profile(other, business_name="Other Co 2")
    product = _make_product(owner_profile.id)

    with pytest.raises(ProductNotFoundError):
        product_service.update_product(
            product.id, other_profile.id, "Hacked Name", ProductCategory.OTHER, 999, ProductUnit.EACH
        )


def test_archive_product_sets_is_archived(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    archived = product_service.archive_product(product.id, profile.id)

    assert archived.is_archived is True


# --- Service: bulk price adjustment -----------------------------------------


def test_bulk_adjust_price_percentage_increase(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A", price_cents=1000)
    p2 = _make_product(profile.id, name="B", price_cents=2000)

    product_service.bulk_adjust_price([p1.id, p2.id], profile.id, "INCREASE", "PERCENTAGE", 10)

    assert ProductRepository.get_by_id(p1.id).price_cents == 1100
    assert ProductRepository.get_by_id(p2.id).price_cents == 2200


def test_bulk_adjust_price_fixed_decrease(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A", price_cents=1000)

    product_service.bulk_adjust_price([p1.id], profile.id, "DECREASE", "FIXED", 300)

    assert ProductRepository.get_by_id(p1.id).price_cents == 700


def test_bulk_adjust_price_clamps_at_zero_never_negative(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A", price_cents=100)

    product_service.bulk_adjust_price([p1.id], profile.id, "DECREASE", "FIXED", 500)

    assert ProductRepository.get_by_id(p1.id).price_cents == 0


def test_bulk_adjust_price_excludes_other_suppliers_products(make_supplier, make_supplier_profile):
    owner = make_supplier("owner3@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Owner Co 3")
    other = make_supplier("other3@example.com")
    other_profile = make_supplier_profile(other, business_name="Other Co 3")
    victim_product = _make_product(other_profile.id, name="Not Yours", price_cents=1000)

    result = product_service.bulk_adjust_price(
        [victim_product.id], owner_profile.id, "INCREASE", "PERCENTAGE", 50
    )

    assert result == []
    assert ProductRepository.get_by_id(victim_product.id).price_cents == 1000


def test_bulk_archive_only_affects_owned_products(make_supplier, make_supplier_profile):
    owner = make_supplier("owner4@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Owner Co 4")
    other = make_supplier("other4@example.com")
    other_profile = make_supplier_profile(other, business_name="Other Co 4")
    mine = _make_product(owner_profile.id, name="Mine")
    theirs = _make_product(other_profile.id, name="Theirs")

    product_service.bulk_archive([mine.id, theirs.id], owner_profile.id)

    assert ProductRepository.get_by_id(mine.id).is_archived is True
    assert ProductRepository.get_by_id(theirs.id).is_archived is False
