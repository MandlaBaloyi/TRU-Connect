"""
Inventory HTTP-layer tests -- real requests through the real Flask
test client, same pattern as products/test_products_api.py.
"""
from __future__ import annotations

from flask_jwt_extended import create_access_token

from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def _auth(user, role: str) -> dict:
    return {"Authorization": f"Bearer {_token_for(user, role)}"}


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


# --- List / detail / summary --------------------------------------------


def test_list_inventory_returns_composed_shape(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    _make_product(profile.id)

    response = client.get("/api/v1/supplier-discovery/inventory", headers=_auth(supplier, "supplier"))

    assert response.status_code == 200
    results = response.get_json()["data"]["results"]
    assert len(results) == 1
    item = results[0]
    assert item["product"]["name"] == "Coca-Cola 500ml"
    # Real gap found during frontend wiring: this field used to be
    # missing from the inventory route's own response entirely, even
    # though the Inventory screens now display it.
    assert item["product"]["product_code"].startswith("TRU-")
    assert item["inventory"]["quantity_on_hand"] == 0
    assert item["status"] == "OUT_OF_STOCK"
    assert item["available_quantity"] == 0


def test_get_inventory_item_not_found_for_other_suppliers_product(client, make_supplier, make_supplier_profile):
    owner = make_supplier("inv-http-owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="HTTP Owner Co")
    other = make_supplier("inv-http-other@example.com")
    make_supplier_profile(other, business_name="HTTP Other Co")
    product = _make_product(owner_profile.id)

    response = client.get(
        f"/api/v1/supplier-discovery/inventory/{product.id}", headers=_auth(other, "supplier")
    )

    assert response.status_code == 404


def test_get_summary_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A")
    client.post(
        f"/api/v1/supplier-discovery/inventory/{p1.id}/adjust",
        json={"quantity_delta": 20, "reason": "STOCK_RECEIVED"},
        headers=_auth(supplier, "supplier"),
    )

    response = client.get("/api/v1/supplier-discovery/inventory/summary", headers=_auth(supplier, "supplier"))

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["total_products"] == 1
    assert data["in_stock_count"] == 1


# --- Adjust / threshold --------------------------------------------------


def test_adjust_stock_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    response = client.post(
        f"/api/v1/supplier-discovery/inventory/{product.id}/adjust",
        json={"quantity_delta": 30, "reason": "STOCK_RECEIVED"},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["inventory"]["quantity_on_hand"] == 30
    assert data["status"] == "IN_STOCK"


def test_adjust_stock_below_zero_returns_409(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    response = client.post(
        f"/api/v1/supplier-discovery/inventory/{product.id}/adjust",
        json={"quantity_delta": -5, "reason": "STOCK_SOLD"},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 409
    body = response.get_json()
    assert body["code"] == "INSUFFICIENT_STOCK"


def test_adjust_stock_rejects_invalid_reason(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    response = client.post(
        f"/api/v1/supplier-discovery/inventory/{product.id}/adjust",
        json={"quantity_delta": 5, "reason": "NOT_A_REAL_REASON"},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_set_threshold_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    response = client.put(
        f"/api/v1/supplier-discovery/inventory/{product.id}/threshold",
        json={"low_stock_threshold": 25},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["inventory"]["low_stock_threshold"] == 25


def test_set_threshold_rejects_negative(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    response = client.put(
        f"/api/v1/supplier-discovery/inventory/{product.id}/threshold",
        json={"low_stock_threshold": -1},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


# --- Settings --------------------------------------------------------------


def test_get_and_update_settings_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    make_supplier_profile(supplier)

    initial = client.get("/api/v1/supplier-discovery/inventory/settings", headers=_auth(supplier, "supplier"))
    assert initial.status_code == 200
    assert initial.get_json()["data"]["default_low_stock_threshold"] == 5
    assert initial.get_json()["data"]["low_stock_alert_channel"] == "IN_APP"

    updated = client.put(
        "/api/v1/supplier-discovery/inventory/settings",
        json={"default_low_stock_threshold": 10, "low_stock_alert_channel": "EMAIL"},
        headers=_auth(supplier, "supplier"),
    )
    assert updated.status_code == 200
    data = updated.get_json()["data"]
    assert data["default_low_stock_threshold"] == 10
    assert data["low_stock_alert_channel"] == "EMAIL"


def test_new_product_inventory_seeded_with_updated_default_threshold(client, make_supplier, make_supplier_profile):
    """The default threshold setting actually affects NEW products'
    inventory records -- this is the whole reason the setting exists."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    client.put(
        "/api/v1/supplier-discovery/inventory/settings",
        json={"default_low_stock_threshold": 40},
        headers=_auth(supplier, "supplier"),
    )
    product = _make_product(profile.id, name="Seeded After Setting")

    response = client.get(
        f"/api/v1/supplier-discovery/inventory/{product.id}", headers=_auth(supplier, "supplier")
    )

    assert response.get_json()["data"]["inventory"]["low_stock_threshold"] == 40


# --- Auth --------------------------------------------------------------


def test_business_role_is_rejected(client, make_business):
    business = make_business()

    response = client.get("/api/v1/supplier-discovery/inventory", headers=_auth(business, "business"))

    assert response.status_code == 403


def test_unauthenticated_request_is_rejected(client):
    response = client.get("/api/v1/supplier-discovery/inventory")

    assert response.status_code == 401
