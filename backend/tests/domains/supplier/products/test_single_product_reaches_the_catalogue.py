"""
A product added ONE AT A TIME must reach the shared catalogue.

THE GAP THESE CLOSE. Until 2026-09-11 only bulk import called
match_and_link, and the single-product form accepted no barcode, brand
or pack columns at all. A supplier adding twenty products by hand --
precisely the small supplier V2_03 says the product courts first --
produced offers with no product_id: invisible to price comparison,
buy-it-again, and every other feature the catalogue exists to power.

Two halves, and both were broken: the form could not CARRY the
identity, and nothing MATCHED it.
"""
from __future__ import annotations

import pytest

from src.domains.catalogue.products.models.product import Product
from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
from src.domains.supplier.products.services import product_service


@pytest.fixture()
def profile(make_supplier, make_supplier_profile):
    return make_supplier_profile(make_supplier())


def _create(profile, **overrides):
    kwargs = dict(
        supplier_profile_id=profile.id,
        name="Coca-Cola Original 2L",
        category=ProductCategory.BEVERAGES,
        price_cents=2200,
        selling_unit=ProductUnit.EACH,
    )
    kwargs.update(overrides)
    return product_service.create_product(**kwargs)


def test_a_hand_added_product_joins_the_catalogue(profile):
    """It used to end up with product_id None, forever."""
    offer = _create(profile)

    assert offer.product_id is not None, "the offer reached the catalogue"
    assert Product.query.count() == 1


def test_a_hand_added_barcode_is_actually_used(profile):
    """The form could not even carry a barcode before this."""
    offer = _create(profile, barcode="5449000054227")

    product = Product.query.one()
    assert offer.product_id == product.id
    assert product.gtin == "5449000054227", "the barcode reached the shared catalogue"


def test_a_second_supplier_lands_on_the_same_product_by_barcode(
    make_supplier, make_supplier_profile
):
    """THE WHOLE POINT. Two suppliers, two hand-typed spellings, one
    barcode -- and one catalogue product, which is what makes "who sells
    this cheaper" answerable."""
    a = make_supplier_profile(make_supplier("a@example.com"), business_name="A Wholesale")
    b = make_supplier_profile(make_supplier("b@example.com"), business_name="B Distributors")

    first = _create(a, barcode="5449000054227")
    second = product_service.create_product(
        supplier_profile_id=b.id,
        name="COKE 2LT PET",
        category=ProductCategory.BEVERAGES,
        price_cents=2450,
        selling_unit=ProductUnit.EACH,
        barcode="5449000054227",
    )

    assert Product.query.count() == 1, "the barcode matched; no second product invented"
    assert first.product_id == second.product_id


def test_an_in_store_barcode_never_reaches_the_catalogue(profile):
    """A restricted-circulation code is unique only inside one shop.
    Admitting one would let the next shop's unrelated product link to
    this one at confidence 1.0."""
    offer = _create(profile, barcode="2000001000007")

    product = Product.query.one()
    assert offer.product_id == product.id, "the offer still matched on its text"
    assert product.gtin is None, "but the in-store code was not claimed as an identifier"


def test_matching_failure_never_loses_the_product(profile, monkeypatch):
    """The offer is already saved when matching runs. A matching problem
    must cost the supplier nothing -- the same rule the import worker
    has always followed."""
    def boom(**kwargs):
        raise RuntimeError("matching exploded")

    monkeypatch.setattr(
        "src.domains.catalogue.matching.services.linking_service.match_and_link", boom
    )

    offer = _create(profile)

    assert offer.id is not None, "the product still exists"
    assert offer.name == "Coca-Cola Original 2L"
