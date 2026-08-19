"""
Products HTTP-layer tests -- real requests through the real Flask test
client, matching connections/test_api.py's own approach (drive
everything through `client`, not the service layer directly).

role_required("supplier") is exercised directly (test_business_role_is_
rejected), same reasoning connections/test_api.py's own
test_supplier_role_is_rejected gives for why that's worth its own test,
not just trusting the decorator is present.
"""
from __future__ import annotations

from flask_jwt_extended import create_access_token

from src.domains.supplier.products.models.product import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_repository import ProductRepository


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def _auth(user, role: str) -> dict:
    return {"Authorization": f"Bearer {_token_for(user, role)}"}


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


# --- Create ------------------------------------------------------------


def test_create_product_returns_201_with_full_dto(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    make_supplier_profile(supplier)

    response = client.post(
        "/api/v1/supplier-discovery/products",
        json={"name": "Bread", "category": "BAKERY", "price_cents": 1999, "selling_unit": "EACH"},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["success"] is True
    data = body["data"]
    assert data["name"] == "Bread"
    assert data["category"] == "BAKERY"
    assert data["price_cents"] == 1999
    assert data["images"] == []
    assert data["is_archived"] is False


def test_create_product_validation_error_returns_422(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    make_supplier_profile(supplier)

    response = client.post(
        "/api/v1/supplier-discovery/products",
        json={"name": "", "category": "BAKERY", "price_cents": 100, "selling_unit": "EACH"},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_create_product_rejects_unknown_category(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    make_supplier_profile(supplier)

    response = client.post(
        "/api/v1/supplier-discovery/products",
        json={"name": "Bread", "category": "NOT_A_REAL_CATEGORY", "price_cents": 100, "selling_unit": "EACH"},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_business_role_is_rejected_from_create(client, make_business):
    business = make_business()

    response = client.post(
        "/api/v1/supplier-discovery/products",
        json={"name": "Bread", "category": "BAKERY", "price_cents": 100, "selling_unit": "EACH"},
        headers=_auth(business, "business"),
    )

    assert response.status_code == 403


def test_unauthenticated_request_is_rejected(client):
    response = client.post(
        "/api/v1/supplier-discovery/products",
        json={"name": "Bread", "category": "BAKERY", "price_cents": 100, "selling_unit": "EACH"},
    )

    assert response.status_code == 401


# --- List / Get ------------------------------------------------------------


def test_list_products_excludes_archived_by_default(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    _make_product(profile.id, name="Active")
    archived = _make_product(profile.id, name="Archived")
    ProductRepository.archive(archived)

    response = client.get("/api/v1/supplier-discovery/products", headers=_auth(supplier, "supplier"))

    assert response.status_code == 200
    results = response.get_json()["data"]["results"]
    names = {r["name"] for r in results}
    assert names == {"Active"}


def test_list_products_only_returns_own_products(client, make_supplier, make_supplier_profile):
    owner = make_supplier("owner5@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Owner Co 5")
    other = make_supplier("other5@example.com")
    other_profile = make_supplier_profile(other, business_name="Other Co 5")
    _make_product(owner_profile.id, name="Mine")
    _make_product(other_profile.id, name="Not Mine")

    response = client.get("/api/v1/supplier-discovery/products", headers=_auth(owner, "supplier"))

    names = {r["name"] for r in response.get_json()["data"]["results"]}
    assert names == {"Mine"}


def test_get_product_not_found_for_other_suppliers_product_returns_404(client, make_supplier, make_supplier_profile):
    owner = make_supplier("owner6@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Owner Co 6")
    other = make_supplier("other6@example.com")
    make_supplier_profile(other, business_name="Other Co 6")
    product = _make_product(owner_profile.id)

    response = client.get(f"/api/v1/supplier-discovery/products/{product.id}", headers=_auth(other, "supplier"))

    assert response.status_code == 404


# --- Update / Archive --------------------------------------------------


def test_update_product_persists_changes(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    response = client.patch(
        f"/api/v1/supplier-discovery/products/{product.id}",
        json={"name": "Coca-Cola 1.25L", "category": "BEVERAGES", "price_cents": 2100, "selling_unit": "BOTTLE"},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["name"] == "Coca-Cola 1.25L"


def test_archive_product_returns_archived_dto(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    response = client.post(
        f"/api/v1/supplier-discovery/products/{product.id}/archive", headers=_auth(supplier, "supplier")
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["is_archived"] is True


# --- Bulk --------------------------------------------------------------


def test_bulk_adjust_price_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A", price_cents=1000)

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/adjust-price",
        json={"product_ids": [str(p1.id)], "direction": "INCREASE", "type": "FIXED", "value": 200},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 200
    assert ProductRepository.get_by_id(p1.id).price_cents == 1200


def test_bulk_archive_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A")

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/archive",
        json={"product_ids": [str(p1.id)]},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 200
    assert ProductRepository.get_by_id(p1.id).is_archived is True


def test_bulk_archive_rejects_empty_product_ids(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    make_supplier_profile(supplier)

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/archive",
        json={"product_ids": []},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422
