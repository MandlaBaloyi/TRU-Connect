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
    SupplierOfferRepository.archive(archived)

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


def test_create_product_dto_includes_sku_and_product_code(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    make_supplier_profile(supplier)

    response = client.post(
        "/api/v1/supplier-discovery/products",
        json={"name": "Bread", "category": "BAKERY", "price_cents": 100, "selling_unit": "EACH"},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["sku"] == "SKU-000001"
    assert data["product_code"].startswith("TRU-")


def test_update_product_rejects_a_request_containing_product_code(client, make_supplier, make_supplier_profile):
    """THE REAL GUARANTEE, stronger than initially assumed -- confirmed
    directly: product_code is never declared as a field on
    UpdateProductSchema at all (see product.py's own product_code
    column docstring), and Marshmallow's own default behavior is to
    reject the ENTIRE request outright when it contains a field the
    schema doesn't recognize, rather than silently dropping it. Even a
    request deliberately including a fake product_code never reaches
    the service layer at all."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    original_code = product.product_code

    response = client.patch(
        f"/api/v1/supplier-discovery/products/{product.id}",
        json={
            "name": "Bread",
            "category": "BAKERY",
            "price_cents": 100,
            "selling_unit": "EACH",
            "product_code": "TRU-HACKED",  # attempted injection -- schema doesn't declare this field at all
        },
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422

    # And the real row is confirmed completely untouched by the
    # attempt, not just that the request itself failed.
    unchanged = client.get(
        f"/api/v1/supplier-discovery/products/{product.id}", headers=_auth(supplier, "supplier")
    )
    assert unchanged.get_json()["data"]["product_code"] == original_code


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


def test_unarchive_product_returns_unarchived_dto(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    client.post(f"/api/v1/supplier-discovery/products/{product.id}/archive", headers=_auth(supplier, "supplier"))

    response = client.post(
        f"/api/v1/supplier-discovery/products/{product.id}/unarchive", headers=_auth(supplier, "supplier")
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["is_archived"] is False


def test_unarchive_product_not_found_for_other_suppliers_product(client, make_supplier, make_supplier_profile):
    owner = make_supplier("unarchive-owner@example.com")
    make_supplier_profile(owner, business_name="Unarchive Owner Co")
    other = make_supplier("unarchive-other@example.com")
    other_profile = make_supplier_profile(other, business_name="Unarchive Other Co")
    product = _make_product(other_profile.id)

    response = client.post(
        f"/api/v1/supplier-discovery/products/{product.id}/unarchive", headers=_auth(owner, "supplier")
    )

    assert response.status_code == 404


def test_delete_product_via_http_removes_it_from_the_list(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, name="Delete Me")

    response = client.delete(
        f"/api/v1/supplier-discovery/products/{product.id}", headers=_auth(supplier, "supplier")
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["deleted"] is True

    list_response = client.get("/api/v1/supplier-discovery/products?filter=ALL", headers=_auth(supplier, "supplier"))
    names = {p["name"] for p in list_response.get_json()["data"]["results"]}
    assert "Delete Me" not in names


def test_delete_product_not_found_for_other_suppliers_product(client, make_supplier, make_supplier_profile):
    owner = make_supplier("delete-owner@example.com")
    make_supplier_profile(owner, business_name="Delete Owner Co")
    other = make_supplier("delete-other@example.com")
    other_profile = make_supplier_profile(other, business_name="Delete Other Co")
    product = _make_product(other_profile.id)

    response = client.delete(f"/api/v1/supplier-discovery/products/{product.id}", headers=_auth(owner, "supplier"))

    assert response.status_code == 404


def test_bulk_unarchive_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A")
    client.post(f"/api/v1/supplier-discovery/products/{p1.id}/archive", headers=_auth(supplier, "supplier"))

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/unarchive",
        json={"product_ids": [str(p1.id)]},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 200
    assert SupplierOfferRepository.get_by_id(p1.id).is_archived is False


def test_bulk_delete_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A")

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/delete",
        json={"product_ids": [str(p1.id)]},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 200
    assert SupplierOfferRepository.get_by_id(p1.id) is None  # correctly filtered out now it's deleted


def test_bulk_delete_rejects_empty_product_ids(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    make_supplier_profile(supplier)

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/delete",
        json={"product_ids": []},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_bulk_set_discount_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, name="A", price_cents=1000)

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/discount",
        json={"product_ids": [str(product.id)], "discount_percent": 20},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 200
    data = response.get_json()["data"]["results"][0]
    assert data["compare_at_price_cents"] == 1250
    assert data["price_cents"] == 1000  # untouched


def test_bulk_set_discount_result_includes_a_real_percent_off_badge_worth_of_data(
    client, make_supplier, make_supplier_profile
):
    """Confirms the real end-to-end value a supplier would actually
    see -- the SAME product, fetched fresh afterward, carries both
    fields correctly so the already-built "X% OFF" badge on the list
    screens renders correctly."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, name="Perfume", price_cents=25000)

    client.post(
        "/api/v1/supplier-discovery/products/bulk/discount",
        json={"product_ids": [str(product.id)], "discount_percent": 20},
        headers=_auth(supplier, "supplier"),
    )

    fetched = client.get(
        f"/api/v1/supplier-discovery/products/{product.id}", headers=_auth(supplier, "supplier")
    )
    data = fetched.get_json()["data"]
    assert data["price_cents"] == 25000
    assert data["compare_at_price_cents"] == 31250


def test_bulk_set_discount_rejects_zero_percent_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, price_cents=1000)

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/discount",
        json={"product_ids": [str(product.id)], "discount_percent": 0},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_bulk_set_discount_rejects_100_percent_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, price_cents=1000)

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/discount",
        json={"product_ids": [str(product.id)], "discount_percent": 100},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_bulk_set_discount_rejects_empty_product_ids_via_http(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    make_supplier_profile(supplier)

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/discount",
        json={"product_ids": [], "discount_percent": 20},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_list_products_filter_archived_returns_archived_only_via_http(client, make_supplier, make_supplier_profile):
    """THE REAL BUG found during real device testing, exercised at the
    exact HTTP boundary the real app calls: GET
    /products?filter=ARCHIVED used to return every product, active and
    archived mixed -- because the old include_archived=True only ever
    meant "stop excluding archived," never "show ONLY archived." This
    is the same request the Archived filter tab actually sends."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    active = _make_product(profile.id, name="Active One")
    archived = _make_product(profile.id, name="Archived One")
    client.post(f"/api/v1/supplier-discovery/products/{archived.id}/archive", headers=_auth(supplier, "supplier"))

    response = client.get(
        "/api/v1/supplier-discovery/products?filter=ARCHIVED", headers=_auth(supplier, "supplier")
    )

    assert response.status_code == 200
    names = {p["name"] for p in response.get_json()["data"]["results"]}
    assert names == {"Archived One"}


def test_list_products_default_filter_returns_active_only_via_http(client, make_supplier, make_supplier_profile):
    """The other half of the same fix, confirmed not to have
    regressed: the default/ALL view must keep showing active products
    only, exactly what every "All" tab screenshot throughout this
    whole build has always correctly shown."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    active = _make_product(profile.id, name="Active One")
    archived = _make_product(profile.id, name="Archived One")
    client.post(f"/api/v1/supplier-discovery/products/{archived.id}/archive", headers=_auth(supplier, "supplier"))

    response = client.get("/api/v1/supplier-discovery/products?filter=ALL", headers=_auth(supplier, "supplier"))

    assert response.status_code == 200
    names = {p["name"] for p in response.get_json()["data"]["results"]}
    assert names == {"Active One"}


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
    assert SupplierOfferRepository.get_by_id(p1.id).price_cents == 1200


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
    assert SupplierOfferRepository.get_by_id(p1.id).is_archived is True


def test_bulk_archive_rejects_empty_product_ids(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    make_supplier_profile(supplier)

    response = client.post(
        "/api/v1/supplier-discovery/products/bulk/archive",
        json={"product_ids": []},
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


# --- Pin to business profile -----------------------------------------------


def test_pin_and_unpin_flips_is_pinned_in_the_list(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, name="Feature me")

    def list_is_pinned():
        resp = client.get("/api/v1/supplier-discovery/products", headers=_auth(supplier, "supplier"))
        return resp.get_json()["data"]["results"][0]["is_pinned"]

    assert list_is_pinned() is False

    pin_resp = client.post(
        f"/api/v1/supplier-discovery/products/{product.id}/pin", headers=_auth(supplier, "supplier")
    )
    assert pin_resp.status_code == 200
    assert pin_resp.get_json()["data"]["is_pinned"] is True
    assert list_is_pinned() is True

    unpin_resp = client.delete(
        f"/api/v1/supplier-discovery/products/{product.id}/pin", headers=_auth(supplier, "supplier")
    )
    assert unpin_resp.status_code == 200
    assert unpin_resp.get_json()["data"]["is_pinned"] is False
    assert list_is_pinned() is False


def test_pin_seventh_product_returns_422(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    products = [_make_product(profile.id, name=f"Item {i}") for i in range(7)]

    for product in products[:6]:
        resp = client.post(
            f"/api/v1/supplier-discovery/products/{product.id}/pin", headers=_auth(supplier, "supplier")
        )
        assert resp.status_code == 200

    over = client.post(
        f"/api/v1/supplier-discovery/products/{products[6].id}/pin", headers=_auth(supplier, "supplier")
    )
    assert over.status_code == 422
