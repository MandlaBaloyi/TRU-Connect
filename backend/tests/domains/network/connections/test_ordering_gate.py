"""
Tests for can_place_order (the real ordering gate agreed during
architecture review: ACTIVE connection AND at least one real
product) and list_supplier_products.
"""
from __future__ import annotations

from src.domains.network.connections.models.connection_request import ConnectionRequest, ConnectionRequestStatus
from src.domains.network.connections.services import connections_service
from src.domains.supplier.products.models.product import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.extensions import db


def _make_active_connection(business, supplier_profile):
    connections_service.request_connection(business.id, supplier_profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=supplier_profile.id).first()
    request.status = ConnectionRequestStatus.ACTIVE
    db.session.commit()


def _make_product(profile_id, name, category, price_cents, selling_unit):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    return ProductRepository.create(
        profile_id, name, category, price_cents, selling_unit,
        sku=generate_sku(profile_id), product_code=generate_product_code(),
    )


def test_cannot_order_with_no_connection_and_no_products(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Nothing Yet Co")

    result = connections_service.can_place_order(business.id, profile.id)

    assert result["canOrder"] is False
    assert result["isConnected"] is False
    assert result["hasProducts"] is False
    assert result["reason"] == "NOT_CONNECTED"


def test_cannot_order_when_connected_but_supplier_has_no_products(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Empty Catalogue Co")
    _make_active_connection(business, profile)

    result = connections_service.can_place_order(business.id, profile.id)

    assert result["canOrder"] is False
    assert result["isConnected"] is True
    assert result["hasProducts"] is False
    assert result["reason"] == "SUPPLIER_HAS_NO_PRODUCTS"


def test_cannot_order_when_supplier_has_products_but_not_connected(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Has Stock No Connection Co")
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = connections_service.can_place_order(business.id, profile.id)

    assert result["canOrder"] is False
    assert result["isConnected"] is False
    assert result["hasProducts"] is True
    assert result["reason"] == "NOT_CONNECTED"


def test_can_order_when_both_conditions_are_met(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Ready To Order Co")
    _make_active_connection(business, profile)
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = connections_service.can_place_order(business.id, profile.id)

    assert result["canOrder"] is True
    assert result["reason"] is None


def test_pending_connection_is_not_sufficient(make_business, make_supplier, make_supplier_profile):
    """PENDING is not ACTIVE -- a request that hasn't been approved
    yet must not count as connected for ordering purposes."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Still Pending Co")
    connections_service.request_connection(business.id, profile.id)  # stays PENDING
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = connections_service.can_place_order(business.id, profile.id)

    assert result["canOrder"] is False
    assert result["reason"] == "NOT_CONNECTED"


def test_list_supplier_products_returns_real_products(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Listable Co")
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)
    _make_product(profile.id, "Milk 2L", ProductCategory.DAIRY_CHILLED, 3200, ProductUnit.EACH)

    products = connections_service.list_supplier_products(profile.id)

    assert len(products) == 2
    names = {p["name"] for p in products}
    assert names == {"Bread loaves", "Milk 2L"}

    bread = next(p for p in products if p["name"] == "Bread loaves")
    assert bread["category"] == "BAKERY"
    assert bread["priceCents"] == 2500
    assert bread["sellingUnit"] == "EACH"
    assert bread["images"] == []


def test_list_supplier_products_excludes_archived(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Half Archived Co")
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)
    archived = _make_product(profile.id, "Old Stock", ProductCategory.OTHER, 100, ProductUnit.EACH)
    ProductRepository.archive(archived)

    products = connections_service.list_supplier_products(profile.id)

    names = {p["name"] for p in products}
    assert names == {"Bread loaves"}


def test_get_supplier_profile_includes_real_product_count(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Counted Co")
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = connections_service.get_supplier_profile(business.id, profile.id)

    assert result["productCount"] == 1
