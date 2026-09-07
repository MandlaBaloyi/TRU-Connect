"""
The supplier brand-profile additions the business-facing endpoints
gained: businessImageUrl / coverImageUrl / memberSince on
GET /suppliers/{id}, and the category showcase on
GET /suppliers/{id}/profile-products.
"""
from __future__ import annotations

from flask_jwt_extended import create_access_token

from src.domains.supplier.products.models.product import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_media_repository import ProductMediaRepository
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.supplier_profile.services import pinned_products_service
from src.shared.media.mixins import MediaScanStatus


def _auth(user, role: str = "business") -> dict:
    token = create_access_token(identity=str(user.id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def _make_product(
    profile_id,
    name,
    category=ProductCategory.BEVERAGES,
    *,
    with_image=True,
    compare_at_price_cents=None,
    stock=0,
):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku
    from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository

    product = ProductRepository.create(
        supplier_profile_id=profile_id,
        name=name,
        category=category,
        price_cents=1200,
        selling_unit=ProductUnit.EACH,
        sku=generate_sku(profile_id),
        product_code=generate_product_code(),
        compare_at_price_cents=compare_at_price_cents,
    )
    if stock:
        inventory = InventoryRepository.get_or_create_for_product(product.id, profile_id)
        InventoryRepository.adjust_quantity(inventory, stock)
    if with_image:
        media = ProductMediaRepository.create_pending(
            product.id, f"pub/{product.id}", f"https://x/{product.id}.jpg", "image", "jpg", 100, 100, 500, 0
        )
        ProductMediaRepository.apply_scan_status(media, MediaScanStatus.APPROVED.value, "none", None)
    return product


def _showcase(client, business, profile_id):
    resp = client.get(
        f"/api/v1/supplier-discovery/suppliers/{profile_id}/profile-products", headers=_auth(business)
    )
    assert resp.status_code == 200
    return resp.get_json()["data"]["categories"]


def test_get_supplier_profile_exposes_brand_assets_ungated(
    client, make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user,
        business_name="Brand Co",
        business_image_url="https://res.cloudinary.com/x/biz.jpg",
        cover_image_url="https://res.cloudinary.com/x/cover.jpg",
    )

    resp = client.get(f"/api/v1/supplier-discovery/suppliers/{profile.id}", headers=_auth(business))

    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["businessImageUrl"] == "https://res.cloudinary.com/x/biz.jpg"
    assert data["coverImageUrl"] == "https://res.cloudinary.com/x/cover.jpg"
    assert data["memberSince"] and " " in data["memberSince"]  # "<Month> <Year>"


def test_showcase_groups_by_category_biggest_first_and_drops_imageless(
    client, make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Store Co")

    _make_product(profile.id, "Coke", ProductCategory.BEVERAGES)
    _make_product(profile.id, "Fanta", ProductCategory.BEVERAGES)
    _make_product(profile.id, "Chips", ProductCategory.SNACKS_CONFECTIONERY)
    _make_product(profile.id, "Soap", ProductCategory.PERSONAL_CARE)
    _make_product(profile.id, "No photo yet", ProductCategory.PERSONAL_CARE, with_image=False)

    categories = _showcase(client, business, profile.id)

    # BEVERAGES (2 imaged) first; PERSONAL_CARE and SNACKS tie at 1, so the
    # canonical ProductCategory order breaks it (SNACKS_CONFECTIONERY before
    # PERSONAL_CARE).
    assert [c["category"] for c in categories] == ["BEVERAGES", "SNACKS_CONFECTIONERY", "PERSONAL_CARE"]
    beverages = next(c for c in categories if c["category"] == "BEVERAGES")
    assert {p["name"] for p in beverages["products"]} == {"Coke", "Fanta"}
    personal = next(c for c in categories if c["category"] == "PERSONAL_CARE")
    assert [p["name"] for p in personal["products"]] == ["Soap"]  # imageless one excluded


def test_showcase_puts_pinned_product_first_in_its_category(
    client, make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Pin Co")
    _make_product(profile.id, "First listed", ProductCategory.BEVERAGES)
    pinned = _make_product(profile.id, "Pinned pick", ProductCategory.BEVERAGES)
    pinned_products_service.pin(profile.id, pinned.id)

    categories = _showcase(client, business, profile.id)

    beverages = next(c for c in categories if c["category"] == "BEVERAGES")
    assert beverages["products"][0]["name"] == "Pinned pick"


def test_showcase_ranks_in_stock_above_out_of_stock(
    client, make_business, make_supplier, make_supplier_profile
):
    """An out-of-stock product in a shopfront strip is a dead end -- it
    still appears (honestly badged), just never above something a
    business can actually order right now."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Stock Rank Co")
    # Listed FIRST (so newest-first ordering would otherwise put it on
    # top) but has no inventory at all.
    _make_product(profile.id, "Sold out", ProductCategory.BEVERAGES, stock=0)
    _make_product(profile.id, "Available", ProductCategory.BEVERAGES, stock=5)

    categories = _showcase(client, business, profile.id)

    beverages = next(c for c in categories if c["category"] == "BEVERAGES")
    names = [p["name"] for p in beverages["products"]]
    assert names == ["Available", "Sold out"]


def test_showcase_ranks_deeper_discount_first(
    client, make_business, make_supplier, make_supplier_profile
):
    """A real compare-at price is the strongest "look at this" signal a
    supplier gives for free -- deeper discounts lead their strip."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Discount Rank Co")
    # All in stock, so stock isn't what's being measured here.
    _make_product(profile.id, "No discount", ProductCategory.BEVERAGES, stock=5)
    _make_product(profile.id, "Small discount", ProductCategory.BEVERAGES, stock=5, compare_at_price_cents=1400)
    _make_product(profile.id, "Big discount", ProductCategory.BEVERAGES, stock=5, compare_at_price_cents=3000)

    categories = _showcase(client, business, profile.id)

    beverages = next(c for c in categories if c["category"] == "BEVERAGES")
    names = [p["name"] for p in beverages["products"]]
    assert names == ["Big discount", "Small discount", "No discount"]


def test_showcase_ignores_a_compare_at_price_that_is_not_a_real_discount(
    client, make_business, make_supplier, make_supplier_profile
):
    """A compare-at at or BELOW the selling price is stale or
    mis-entered data, never a discount -- it must not rank a product up.
    Both products here tie on every signal, so the caller's own
    newest-first order decides."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Bad Compare Co")
    _make_product(profile.id, "Listed first", ProductCategory.BEVERAGES, stock=5)
    # price_cents is 1200; a compare-at of 900 is not a markdown.
    _make_product(profile.id, "Listed second", ProductCategory.BEVERAGES, stock=5, compare_at_price_cents=900)

    categories = _showcase(client, business, profile.id)

    beverages = next(c for c in categories if c["category"] == "BEVERAGES")
    assert [p["name"] for p in beverages["products"]] == ["Listed second", "Listed first"]


def test_showcase_pin_outranks_stock_and_discount(
    client, make_business, make_supplier, make_supplier_profile
):
    """The supplier's own explicit "feature this" beats every computed
    signal -- including being out of stock. Pinning stays entirely
    optional; this is what it buys a supplier who does use it."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Pin Wins Co")
    _make_product(profile.id, "In stock and discounted", ProductCategory.BEVERAGES, stock=5, compare_at_price_cents=3000)
    pinned = _make_product(profile.id, "Pinned but sold out", ProductCategory.BEVERAGES, stock=0)
    pinned_products_service.pin(profile.id, pinned.id)

    categories = _showcase(client, business, profile.id)

    beverages = next(c for c in categories if c["category"] == "BEVERAGES")
    assert beverages["products"][0]["name"] == "Pinned but sold out"


def test_showcase_caps_at_five_categories(client, make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Wide Co")
    for cat in [
        ProductCategory.BEVERAGES,
        ProductCategory.SNACKS_CONFECTIONERY,
        ProductCategory.PERSONAL_CARE,
        ProductCategory.BAKERY,
        ProductCategory.DAIRY_CHILLED,
        ProductCategory.FRESH_PRODUCE,
        ProductCategory.HOUSEHOLD_CLEANING,
    ]:
        _make_product(profile.id, f"{cat.value} item", cat)

    categories = _showcase(client, business, profile.id)

    assert len(categories) == 5


# --- Activity sharing: the gate is the field's ABSENCE ---------------------


def test_profile_omits_activity_unless_the_supplier_switched_it_on(
    client, make_business, make_supplier, make_supplier_profile
):
    """A field that isn't in the response can't be leaked by a frontend
    that forgets to check a flag -- see discovery_service._resolve_last_active."""
    from src.core.base_model import utcnow
    from src.domains.network.connections.services import discovery_service
    from src.extensions import db

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Private Activity Co")
    supplier_user.last_active_at = utcnow()
    profile.show_last_active = False
    db.session.commit()

    result = discovery_service.get_supplier_profile(business.id, profile.id)
    assert result["activity"] is None


def test_profile_exposes_activity_when_the_supplier_opted_in(
    client, make_business, make_supplier, make_supplier_profile
):
    from src.core.base_model import utcnow
    from src.domains.network.connections.services import discovery_service
    from src.extensions import db

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Shared Activity Co")
    supplier_user.last_active_at = utcnow()
    profile.show_last_active = True
    db.session.commit()

    result = discovery_service.get_supplier_profile(business.id, profile.id)
    assert result["activity"]["isOnline"] is True
    assert result["activity"]["lastActiveAt"]


def test_activity_is_none_when_opted_in_but_never_active(
    client, make_business, make_supplier, make_supplier_profile
):
    """Opting in doesn't invent activity that never happened."""
    from src.domains.network.connections.services import discovery_service
    from src.extensions import db

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Never Active Co")
    profile.show_last_active = True
    db.session.commit()

    result = discovery_service.get_supplier_profile(business.id, profile.id)
    assert result["activity"] is None


def test_trust_counts_only_accepted_orders_and_repeat_buyers(
    client, make_business, make_supplier, make_supplier_profile
):
    """Counts that only grow -- see StockOrderRepository.trust_stats_for_supplier
    on why the earlier ratio and median reply time were removed."""
    from src.domains.network.connections.services import discovery_service

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Fresh Trust Co")

    result = discovery_service.get_supplier_profile(business.id, profile.id)
    # A brand-new supplier reports zeroes; the frontend hides each at 0
    # rather than the backend inventing a floor.
    assert result["trust"] == {"acceptedOrderCount": 0, "repeatBusinessCount": 0, "unitsSoldCount": 0}


def test_track_record_is_omitted_when_the_supplier_switched_it_off(
    client, make_business, make_supplier, make_supplier_profile
):
    """The gate is the field's ABSENCE, same as activity -- a frontend
    that forgets to check a flag can't leak what isn't there."""
    from src.domains.network.connections.services import discovery_service
    from src.extensions import db

    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Private Record Co")
    profile.show_track_record = False
    db.session.commit()

    assert discovery_service.get_supplier_profile(business.id, profile.id)["trust"] is None


def test_track_record_defaults_to_visible(
    client, make_business, make_supplier, make_supplier_profile
):
    """Defaults ON, unlike show_last_active -- every public figure is a
    count that hides at zero, so there is no arrangement of the data
    that can make a supplier look bad by default."""
    from src.domains.network.connections.services import discovery_service

    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Default Record Co")
    assert profile.show_track_record is True

    trust = discovery_service.get_supplier_profile(business.id, profile.id)["trust"]
    assert trust == {"acceptedOrderCount": 0, "repeatBusinessCount": 0, "unitsSoldCount": 0}


def test_supplier_performance_excludes_business_initiated_cancellations(
    make_business, make_supplier, make_supplier_profile
):
    """A business changing its mind is not the supplier's record."""
    from src.core.base_model import utcnow
    from src.domains.network.orders.models.stock_order import StockOrder, StockOrderStatus
    from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository
    from src.extensions import db

    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Cancel Attribution Co")

    for cancelled_by in ("business", "supplier"):
        db.session.add(
            StockOrder(
                business_id=business.id,
                supplier_profile_id=profile.id,
                status=StockOrderStatus.CANCELLED,
                total_cents=1000,
                submitted_at=utcnow(),
                cancelled_by=cancelled_by,
                cancelled_at=utcnow(),
            )
        )
    db.session.commit()

    stats = StockOrderRepository.performance_stats_for_supplier(profile.id)
    assert stats["cancelledAfterConfirming"] == 1
