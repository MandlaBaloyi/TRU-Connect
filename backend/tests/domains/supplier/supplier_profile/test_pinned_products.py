"""
pinned_products_service tests -- the supplier's "feature on my profile"
curation. The business-facing showcase grouping (which consumes
list_pinned_product_ids) is tested in
tests/domains/network/connections/test_profile_products.py.
"""
from __future__ import annotations

import pytest

from src.core.exceptions import NotFoundError
from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.domains.supplier.supplier_profile.services import pinned_products_service
from src.domains.supplier.supplier_profile.services.errors import ProfileValidationError


def _make_product(profile_id, name="Coke 500ml", **overrides):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    defaults = dict(
        supplier_profile_id=profile_id,
        name=name,
        category=ProductCategory.BEVERAGES,
        price_cents=1200,
        selling_unit=ProductUnit.EACH,
        sku=generate_sku(profile_id),
        product_code=generate_product_code(),
    )
    defaults.update(overrides)
    return SupplierOfferRepository.create(**defaults)


def test_pin_then_list_pinned_ids(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    pinned_products_service.pin(profile.id, product.id)

    assert product.id in pinned_products_service.list_pinned_product_ids(profile.id)
    assert pinned_products_service.is_pinned(profile.id, product.id) is True


def test_pin_is_idempotent(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    pinned_products_service.pin(profile.id, product.id)
    pinned_products_service.pin(profile.id, product.id)  # again -- no error, no dup

    assert pinned_products_service.list_pinned_product_ids(profile.id) == {product.id}


def test_unpin(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    pinned_products_service.pin(profile.id, product.id)

    pinned_products_service.unpin(profile.id, product.id)

    assert pinned_products_service.is_pinned(profile.id, product.id) is False
    pinned_products_service.unpin(profile.id, product.id)  # no-op, no error


def test_pin_rejects_over_the_limit(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    products = [_make_product(profile.id, name=f"Item {i}") for i in range(pinned_products_service.MAX_PINNED + 1)]

    for product in products[: pinned_products_service.MAX_PINNED]:
        pinned_products_service.pin(profile.id, product.id)

    with pytest.raises(ProfileValidationError):
        pinned_products_service.pin(profile.id, products[-1].id)


def test_pin_rejects_another_suppliers_product(make_supplier, make_supplier_profile):
    owner = make_supplier("owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Owner Co")
    other = make_supplier("other@example.com")
    other_profile = make_supplier_profile(other, business_name="Other Co")
    product = _make_product(owner_profile.id)

    with pytest.raises(NotFoundError):
        pinned_products_service.pin(other_profile.id, product.id)


def test_pin_rejects_archived_product(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    SupplierOfferRepository.archive(product)

    with pytest.raises(ProfileValidationError):
        pinned_products_service.pin(profile.id, product.id)


def test_list_pinned_product_ids_reflects_pins(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    a = _make_product(profile.id, name="A")
    b = _make_product(profile.id, name="B")
    _make_product(profile.id, name="C")

    pinned_products_service.pin(profile.id, a.id)
    pinned_products_service.pin(profile.id, b.id)

    assert pinned_products_service.list_pinned_product_ids(profile.id) == {a.id, b.id}
