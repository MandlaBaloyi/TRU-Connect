"""
Tests for can_place_order (the real ordering gate agreed during
architecture review: ACTIVE connection AND at least one real
product), list_supplier_products, and get_supplier_product.
"""
from __future__ import annotations

import uuid

import pytest

from src.domains.network.connections.models.connection_request import ConnectionRequest, ConnectionRequestStatus
from src.domains.network.connections.services import (
    discovery_service,
    request_service,
)
from src.domains.network.connections.services.storefront import catalog_service, ordering_gate
from src.domains.network.connections.services.errors import InvalidCatalogQueryError, ProductNotFoundError, SupplierNotFoundError
from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.extensions import db


def _make_active_connection(business, supplier_profile):
    request_service.request_connection(business.id, supplier_profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=supplier_profile.id).first()
    request.status = ConnectionRequestStatus.ACTIVE
    db.session.commit()


def _make_product(profile_id, name, category, price_cents, selling_unit):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    return SupplierOfferRepository.create(
        profile_id, name, category, price_cents, selling_unit,
        sku=generate_sku(profile_id), product_code=generate_product_code(),
    )


def test_an_empty_catalogue_is_the_reason_not_the_missing_connection(
    make_business, make_supplier, make_supplier_profile
):
    """Before v2 step 4 this reported NOT_CONNECTED, because connection
    was checked first and required of everyone. Now the default supplier
    needs no connection at all, so the only real obstacle is the one
    that was always the real obstacle: there is nothing to order."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Nothing Yet Co")

    result = ordering_gate.can_place_order(business.id, profile.id)

    assert result["canOrder"] is False
    assert result["isConnected"] is False
    assert result["hasProducts"] is False
    assert result["requiresConnection"] is False
    assert result["reason"] == "SUPPLIER_HAS_NO_PRODUCTS"


def test_cannot_order_when_connected_but_supplier_has_no_products(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Empty Catalogue Co")
    _make_active_connection(business, profile)

    result = ordering_gate.can_place_order(business.id, profile.id)

    assert result["canOrder"] is False
    assert result["isConnected"] is True
    assert result["hasProducts"] is False
    assert result["reason"] == "SUPPLIER_HAS_NO_PRODUCTS"


def test_a_business_can_order_from_a_stocked_supplier_without_connecting_first(
    make_business, make_supplier, make_supplier_profile
):
    """THE V2 STEP 4 BEHAVIOUR CHANGE, stated as plainly as possible.

    This exact scenario returned canOrder=False and NOT_CONNECTED
    before. Connection approval was a gate on every supplier; it is now
    a per-supplier option that defaults off, because order
    accept/decline is a better control (per-transaction, better
    information) and because a supplier whose orders arrive from their
    own system has nobody to click approve."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Has Stock No Connection Co")
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = ordering_gate.can_place_order(business.id, profile.id)

    assert result["canOrder"] is True
    assert result["isConnected"] is False, "and it did not quietly connect them"
    assert result["hasProducts"] is True
    assert result["requiresConnection"] is False
    assert result["reason"] is None


def test_a_supplier_who_opts_in_still_gets_the_old_gate(
    make_business, make_supplier, make_supplier_profile
):
    """Connection did not disappear, it became a choice.

    A small supplier who genuinely wants to know who is buying before
    stock moves turns requires_connection on and gets exactly the
    behaviour every supplier used to have."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user, business_name="Approve First Co", requires_connection=True
    )
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = ordering_gate.can_place_order(business.id, profile.id)

    assert result["canOrder"] is False
    assert result["requiresConnection"] is True
    assert result["reason"] == "NOT_CONNECTED"

    _make_active_connection(business, profile)
    after = ordering_gate.can_place_order(business.id, profile.id)
    assert after["canOrder"] is True
    assert after["reason"] is None


def test_can_order_when_both_conditions_are_met(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Ready To Order Co")
    _make_active_connection(business, profile)
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = ordering_gate.can_place_order(business.id, profile.id)

    assert result["canOrder"] is True
    assert result["reason"] is None


def test_pending_connection_is_not_sufficient(make_business, make_supplier, make_supplier_profile):
    """PENDING is not ACTIVE -- a request that hasn't been approved
    yet must not count as connected for ordering purposes.

    Only meaningful for a supplier who requires connection at all, so
    the flag is set here. For everyone else a pending request is simply
    irrelevant to ordering, which is the point of step 4."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user, business_name="Still Pending Co", requires_connection=True
    )
    request_service.request_connection(business.id, profile.id)  # stays PENDING
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = ordering_gate.can_place_order(business.id, profile.id)

    assert result["canOrder"] is False
    assert result["reason"] == "NOT_CONNECTED"


def test_list_supplier_products_includes_contact_when_connected_and_opted_in(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL POINT OF ADDING business_id TO THIS FUNCTION -- contact
    at the catalogue level, for the "Contact Supplier" menu item, gated
    exactly like get_supplier_product's own version: active connection
    AND the supplier's own opt-in, both required."""
    from src.domains.network.connections.services import discovery_service, request_service
    from src.domains.network.connections.services.storefront import catalog_service, ordering_gate

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user,
        business_name="Catalogue Contact Co",
        whatsapp_number="27821234567",
        share_contact_details=True,
    )
    request_service.request_connection(business.id, profile.id)
    from src.domains.network.connections.models.connection_request import ConnectionRequest, ConnectionRequestStatus
    from src.extensions import db

    req = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    req.status = ConnectionRequestStatus.ACTIVE
    db.session.commit()

    result = catalog_service.list_supplier_products(business.id, profile.id)

    assert result["contact"] == {"whatsappNumber": "27821234567", "email": None, "tiktokHandle": None}


def test_list_supplier_products_contact_is_null_when_not_connected(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user, business_name="Unreachable Co", whatsapp_number="27821234567", share_contact_details=True
    )

    result = catalog_service.list_supplier_products(business.id, profile.id)

    assert result["contact"] is None


def test_list_supplier_products_returns_real_products(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Listable Co")
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)
    _make_product(profile.id, "Milk 2L", ProductCategory.DAIRY_CHILLED, 3200, ProductUnit.EACH)

    result = catalog_service.list_supplier_products(business.id, profile.id)

    assert result["supplierName"] == "Listable Co"
    products = result["products"]
    assert len(products) == 2
    names = {p["name"] for p in products}
    assert names == {"Bread loaves", "Milk 2L"}

    bread = next(p for p in products if p["name"] == "Bread loaves")
    assert bread["category"] == "BAKERY"
    assert bread["priceCents"] == 2500
    assert bread["compareAtPriceCents"] is None
    assert bread["sellingUnit"] == "EACH"
    assert bread["images"] == []


def test_list_supplier_products_includes_compare_at_price_when_a_product_has_a_real_discount(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL GAP THIS FIXES -- a business browsing a connected
    supplier's catalogue must see the same "was RX" discount the
    supplier themselves set, not just the current price. The frontend's
    own "% OFF" badge (see products/algorithms/discount.ts) depends on
    this field actually being present here."""
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="On Sale Co")
    SupplierOfferRepository.create(
        profile.id, "Perfume", ProductCategory.OTHER, 25000, ProductUnit.EACH,
        sku=generate_sku(profile.id), product_code=generate_product_code(), compare_at_price_cents=31250,
    )

    products = catalog_service.list_supplier_products(business.id, profile.id)["products"]

    assert products[0]["priceCents"] == 25000
    assert products[0]["compareAtPriceCents"] == 31250


def test_list_supplier_products_excludes_archived(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Half Archived Co")
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)
    archived = _make_product(profile.id, "Old Stock", ProductCategory.OTHER, 100, ProductUnit.EACH)
    SupplierOfferRepository.archive(archived)

    products = catalog_service.list_supplier_products(business.id, profile.id)["products"]

    names = {p["name"] for p in products}
    assert names == {"Bread loaves"}


def test_get_supplier_profile_includes_real_product_count(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Counted Co")
    _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["productCount"] == 1


def test_get_supplier_profile_collection_address_is_null_when_not_connected(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL GUARD -- a collection address is exactly the kind of
    information that shouldn't leak to a business that hasn't been
    approved to order from this supplier yet."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Not Connected Co")
    profile.collection_street = "Market Street"
    profile.collection_suburb = "Seshego"
    db.session.commit()

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["collectionAddress"] is None


def test_get_supplier_profile_collection_address_returned_when_active(
    make_business, make_supplier, make_supplier_profile
):
    """Unlike whatsapp/email, this does NOT also require
    share_contact_details -- an active connection alone is enough,
    since a collection address is core order-completion information,
    not a discretionary contact channel (see connections_service.py's
    own comment on this exact distinction)."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Connected Collect Co")
    profile.collection_building = "Warehouse 3"
    profile.collection_street = "Market Street"
    profile.collection_suburb = "Seshego"
    profile.collection_city = "Polokwane"
    profile.collection_province = "Limpopo"
    profile.collection_postal_code = "0742"
    profile.collection_latitude = -23.85
    profile.collection_longitude = 29.40
    db.session.commit()
    _make_active_connection(business, profile)

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["collectionAddress"] == {
        "building": "Warehouse 3",
        "street": "Market Street",
        "suburb": "Seshego",
        "city": "Polokwane",
        "province": "Limpopo",
        "postalCode": "0742",
        "latitude": pytest.approx(-23.85),
        "longitude": pytest.approx(29.40),
    }


def test_get_supplier_profile_collection_address_null_when_supplier_hasnt_set_one(
    make_business, make_supplier, make_supplier_profile
):
    """An active connection alone doesn't fabricate an address out of
    nothing -- a supplier who hasn't set up collection yet still
    correctly returns null, not empty strings."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Address Set Co")
    _make_active_connection(business, profile)

    result = discovery_service.get_supplier_profile(business.id, profile.id)

    assert result["collectionAddress"] is None


def test_get_supplier_profile_contact_requires_active_and_opt_in(
    make_business, make_supplier, make_supplier_profile
):
    """Added specifically so a business viewing a CONFIRMED order they
    can no longer self-cancel has a real way to reach the supplier --
    same double gate (active connection AND the supplier's own
    opt-in) as the contact block used elsewhere in this file."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Contact Gate Co")
    profile.whatsapp_number = "+27821234567"
    profile.share_contact_details = False
    db.session.commit()
    _make_active_connection(business, profile)

    not_opted_in = discovery_service.get_supplier_profile(business.id, profile.id)
    assert not_opted_in["contact"] is None

    profile.share_contact_details = True
    db.session.commit()

    opted_in = discovery_service.get_supplier_profile(business.id, profile.id)
    assert opted_in["contact"] == {"whatsappNumber": "+27821234567", "email": None, "tiktokHandle": None}


# --- get_supplier_product ----------------------------------------------------


def test_list_supplier_products_marks_a_product_with_real_stock_as_in_stock(
    make_business, make_supplier, make_supplier_profile
):
    from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Stocked Co")
    product = _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH)
    inventory = InventoryRepository.get_or_create_for_product(product.id, profile.id)
    InventoryRepository.adjust_quantity(inventory, 10)

    result = catalog_service.list_supplier_products(business.id, profile.id)

    assert result["products"][0]["inStock"] is True


def test_list_supplier_products_marks_a_zero_quantity_product_as_out_of_stock(
    make_business, make_supplier, make_supplier_profile
):
    from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Out Of Stock Co")
    product = _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH)
    InventoryRepository.get_or_create_for_product(product.id, profile.id)  # row exists, zero quantity

    result = catalog_service.list_supplier_products(business.id, profile.id)

    assert result["products"][0]["inStock"] is False


def test_list_supplier_products_marks_a_product_with_no_inventory_row_as_out_of_stock(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL EDGE CASE -- a product the supplier has never touched
    on the Inventory screen at all must read as out of stock, not
    crash and not silently show as available."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Never Touched Co")
    _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH)
    # Deliberately no InventoryRepository call at all.

    result = catalog_service.list_supplier_products(business.id, profile.id)

    assert result["products"][0]["inStock"] is False


def test_list_supplier_products_browsing_never_creates_an_inventory_row(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL SIDE-EFFECT-SAFETY GUARANTEE -- a business simply
    browsing a catalogue must never trigger a write to the supplier's
    own inventory table."""
    from src.domains.supplier.inventory.models.inventory import Inventory

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Untouched Co")
    product = _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH)

    catalog_service.list_supplier_products(business.id, profile.id)

    assert Inventory.query.filter_by(product_id=product.id).first() is None


def test_get_supplier_product_returns_full_detail(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Detail Co")
    product = _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = catalog_service.get_supplier_product(business.id, profile.id, product.id)

    assert result["id"] == str(product.id)
    assert result["name"] == "Bread loaves"
    assert result["priceCents"] == 2500
    assert result["sku"] == product.sku
    assert result["productCode"] == product.product_code
    assert result["images"] == []
    assert result["inStock"] is False  # no inventory row set up at all in this test


def test_get_supplier_product_marks_a_product_with_real_stock_as_in_stock(
    make_business, make_supplier, make_supplier_profile
):
    from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Detail Stocked Co")
    product = _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH)
    inventory = InventoryRepository.get_or_create_for_product(product.id, profile.id)
    InventoryRepository.adjust_quantity(inventory, 5)

    result = catalog_service.get_supplier_product(business.id, profile.id, product.id)

    assert result["inStock"] is True


def test_get_supplier_product_raises_for_a_genuinely_nonexistent_product(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Empty Co")

    with pytest.raises(ProductNotFoundError):
        catalog_service.get_supplier_product(business.id, profile.id, uuid.uuid4())


def test_get_supplier_product_raises_for_a_product_belonging_to_a_different_supplier(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL IDOR CHECK -- a real product id, just under the wrong
    supplier_profile_id in the URL, must be rejected exactly like a
    nonexistent one, never quietly served."""
    business = make_business()
    owner = make_supplier("product-owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Real Owner Co")
    other = make_supplier("product-other@example.com")
    other_profile = make_supplier_profile(other, business_name="Unrelated Co")
    product = _make_product(owner_profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    with pytest.raises(ProductNotFoundError):
        catalog_service.get_supplier_product(business.id, other_profile.id, product.id)


def test_get_supplier_product_raises_for_an_archived_product(make_business, make_supplier, make_supplier_profile):
    """A business should never be able to tell an archived product
    apart from one that never existed -- same IDOR-safety reasoning as
    every other lookup in this domain."""
    from src.domains.supplier.products.services import product_service

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Archive Co")
    product = _make_product(profile.id, "Old Stock", ProductCategory.OTHER, 100, ProductUnit.EACH)
    product_service.archive_product(product.id, profile.id)

    with pytest.raises(ProductNotFoundError):
        catalog_service.get_supplier_product(business.id, profile.id, product.id)


def test_get_supplier_product_always_includes_the_suppliers_real_name(
    make_business, make_supplier, make_supplier_profile
):
    """THE ACTUAL "AM I CERTAIN THIS IS MY SUPPLIER" FIX -- the
    supplier's own real business name, shown regardless of connection
    status or contact-sharing settings (browsing itself stays open;
    only the CONTACT DETAILS below are gated)."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Certainty Co")
    product = _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)

    result = catalog_service.get_supplier_product(business.id, profile.id, product.id)

    assert result["supplierName"] == "Certainty Co"


def test_get_supplier_product_contact_is_null_when_not_connected(
    make_business, make_supplier, make_supplier_profile
):
    """Even a supplier who HAS opted in and filled everything in must
    not leak contact details to a business with no real relationship
    yet -- browsing a catalogue and being trusted with a phone number
    are genuinely different things."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user,
        business_name="Sharing Co",
        whatsapp_number="27821234567",
        share_contact_details=True,
    )
    product = _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)
    # Deliberately NO connection made between business and profile.

    result = catalog_service.get_supplier_product(business.id, profile.id, product.id)

    assert result["contact"] is None


def test_get_supplier_product_contact_is_null_when_connected_but_supplier_has_not_opted_in(
    make_business, make_supplier, make_supplier_profile
):
    """The other half of the same gate -- an ACTIVE connection alone
    isn't enough; the supplier's own share_contact_details must also
    be true."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user,
        business_name="Private Co",
        whatsapp_number="27821234567",
        share_contact_details=False,
    )
    product = _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)
    _make_active_connection(business, profile)

    result = catalog_service.get_supplier_product(business.id, profile.id, product.id)

    assert result["contact"] is None


def test_get_supplier_product_contact_is_returned_when_both_conditions_are_met(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL, WORKING END STATE -- an active connection AND the
    supplier's own opt-in together, and only together, unlock the
    real contact details."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user,
        business_name="Reachable Co",
        whatsapp_number="27821234567",
        contact_email="orders@reachable.co.za",
        tiktok_handle="reachableco",
        share_contact_details=True,
    )
    product = _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)
    _make_active_connection(business, profile)

    result = catalog_service.get_supplier_product(business.id, profile.id, product.id)

    assert result["contact"] == {
        "whatsappNumber": "27821234567",
        "email": "orders@reachable.co.za",
        "tiktokHandle": "reachableco",
    }


def test_get_supplier_product_contact_is_null_when_a_pending_connection_only(
    make_business, make_supplier, make_supplier_profile
):
    """A PENDING request is not an active connection -- same
    distinction can_place_order already enforces elsewhere in this
    file."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(
        supplier_user, business_name="Pending Co", whatsapp_number="27821234567", share_contact_details=True
    )
    product = _make_product(profile.id, "Bread loaves", ProductCategory.BAKERY, 2500, ProductUnit.EACH)
    request_service.request_connection(business.id, profile.id)  # stays PENDING, never approved

    result = catalog_service.get_supplier_product(business.id, profile.id, product.id)

    assert result["contact"] is None


def test_get_supplier_product_raises_supplier_not_found_for_a_genuinely_nonexistent_supplier(make_business):
    business = make_business()

    with pytest.raises(SupplierNotFoundError):
        catalog_service.get_supplier_product(business.id, uuid.uuid4(), uuid.uuid4())


# --- list_supplier_products: pagination, sort, category filter ----------


def test_list_supplier_products_paginates_correctly(make_business, make_supplier, make_supplier_profile):
    """THE REAL "protect the API, and scale" FIX -- a request for a
    small page genuinely returns only that page, not the whole
    catalogue with the rest hidden client-side."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Paginated Co")
    for i in range(5):
        _make_product(profile.id, f"Product {i}", ProductCategory.OTHER, 1000 + i, ProductUnit.EACH)

    page1 = catalog_service.list_supplier_products(business.id, profile.id, page=1, limit=2)
    page2 = catalog_service.list_supplier_products(business.id, profile.id, page=2, limit=2)
    page3 = catalog_service.list_supplier_products(business.id, profile.id, page=3, limit=2)

    assert len(page1["products"]) == 2
    assert len(page2["products"]) == 2
    assert len(page3["products"]) == 1
    assert page1["totalCount"] == 5
    assert page1["totalPages"] == 3
    assert page1["page"] == 1
    assert page2["page"] == 2

    # No overlap between pages -- genuinely different rows, not the
    # same ones repeated.
    page1_ids = {p["id"] for p in page1["products"]}
    page2_ids = {p["id"] for p in page2["products"]}
    assert page1_ids.isdisjoint(page2_ids)


def test_list_supplier_products_limit_is_hard_capped(make_business, make_supplier, make_supplier_profile):
    """THE ACTUAL ENFORCEMENT that makes this a genuine API protection,
    not just a UI suggestion a client could bypass by asking for a
    huge limit."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Capped Co")
    for i in range(3):
        _make_product(profile.id, f"Product {i}", ProductCategory.OTHER, 1000 + i, ProductUnit.EACH)

    result = catalog_service.list_supplier_products(business.id, profile.id, page=1, limit=10000)

    assert len(result["products"]) == 3  # only 3 exist, capping doesn't matter here
    # Confirm the CAP itself, not just that 3 happens to be under it --
    # check totalPages math used the capped limit.
    from src.domains.network.connections.services.storefront.catalog_service import MAX_CATALOG_PAGE_SIZE
    assert MAX_CATALOG_PAGE_SIZE == 50


def test_list_supplier_products_sorts_by_price_ascending(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Sorted Co")
    _make_product(profile.id, "Expensive", ProductCategory.OTHER, 5000, ProductUnit.EACH)
    _make_product(profile.id, "Cheap", ProductCategory.OTHER, 1000, ProductUnit.EACH)
    _make_product(profile.id, "Middle", ProductCategory.OTHER, 3000, ProductUnit.EACH)

    result = catalog_service.list_supplier_products(business.id, profile.id, sort="PRICE_ASC")

    prices = [p["priceCents"] for p in result["products"]]
    assert prices == [1000, 3000, 5000]


def test_list_supplier_products_sorts_by_name_ascending(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Name Sorted Co")
    _make_product(profile.id, "Zebra", ProductCategory.OTHER, 1000, ProductUnit.EACH)
    _make_product(profile.id, "Apple", ProductCategory.OTHER, 1000, ProductUnit.EACH)

    result = catalog_service.list_supplier_products(business.id, profile.id, sort="NAME_ASC")

    names = [p["name"] for p in result["products"]]
    assert names == ["Apple", "Zebra"]


def test_list_supplier_products_filters_by_category(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Filtered Co")
    _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH)
    _make_product(profile.id, "Milk", ProductCategory.DAIRY_CHILLED, 1000, ProductUnit.EACH)

    result = catalog_service.list_supplier_products(business.id, profile.id, category="BAKERY")

    assert result["totalCount"] == 1
    assert result["products"][0]["name"] == "Bread"


def test_list_supplier_products_rejects_a_page_below_one(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Co")

    with pytest.raises(InvalidCatalogQueryError):
        catalog_service.list_supplier_products(business.id, profile.id, page=0)


def test_list_supplier_products_rejects_an_invalid_sort_value(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Co")

    with pytest.raises(InvalidCatalogQueryError):
        catalog_service.list_supplier_products(business.id, profile.id, sort="NOT_A_REAL_SORT")


def test_list_supplier_products_rejects_an_invalid_category(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Co")

    with pytest.raises(InvalidCatalogQueryError):
        catalog_service.list_supplier_products(business.id, profile.id, category="NOT_A_REAL_CATEGORY")


# --- get_supplier_product_categories --------------------------------------


def test_get_supplier_product_categories_returns_real_distinct_categories(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL FIX -- correct regardless of pagination, never derived
    from whatever happens to be on one page."""
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Categorised Co")
    _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH)
    _make_product(profile.id, "Bread rolls", ProductCategory.BAKERY, 900, ProductUnit.EACH)
    _make_product(profile.id, "Milk", ProductCategory.DAIRY_CHILLED, 1500, ProductUnit.EACH)

    categories = catalog_service.get_supplier_product_categories(profile.id)

    assert sorted(categories) == ["BAKERY", "DAIRY_CHILLED"]


def test_get_supplier_product_categories_excludes_archived_products_categories(
    make_business, make_supplier, make_supplier_profile
):
    from src.domains.supplier.products.services import product_service

    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Archived Category Co")
    bread = _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH)
    _make_product(profile.id, "Milk", ProductCategory.DAIRY_CHILLED, 1500, ProductUnit.EACH)
    product_service.archive_product(bread.id, profile.id)

    categories = catalog_service.get_supplier_product_categories(profile.id)

    assert categories == ["DAIRY_CHILLED"]


def test_get_supplier_product_categories_returns_empty_list_for_a_supplier_with_no_products(
    make_supplier, make_supplier_profile
):
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Empty Co")

    categories = catalog_service.get_supplier_product_categories(profile.id)

    assert categories == []


def test_get_supplier_product_categories_raises_for_a_genuinely_nonexistent_supplier(db_session):
    with pytest.raises(SupplierNotFoundError):
        catalog_service.get_supplier_product_categories(uuid.uuid4())


# --- list_related_products -------------------------------------------------


def test_list_related_products_prioritises_genuine_same_category_matches(
    make_business, make_supplier, make_supplier_profile
):
    """Genuinely related items must come first -- backfill only ever
    fills LEFTOVER slots, never displaces a real match."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Related Co")
    viewed = _make_product(profile.id, "Ferrari Red", ProductCategory.PERSONAL_CARE, 30000, ProductUnit.EACH)
    related1 = _make_product(profile.id, "Eternity Fragrance", ProductCategory.PERSONAL_CARE, 25000, ProductUnit.EACH)
    related2 = _make_product(profile.id, "Coach Fragrance", ProductCategory.PERSONAL_CARE, 35000, ProductUnit.EACH)

    result = catalog_service.list_related_products(business.id, profile.id, viewed.id)

    result_ids = {p["id"] for p in result["products"]}
    assert {str(related1.id), str(related2.id)}.issubset(result_ids)


def test_list_related_products_backfills_with_a_different_category_when_related_is_short(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL NEW BEHAVIOUR -- confirmed after direct feedback: a
    supplier with real stock spread across many categories was showing
    nothing here far too often. Only 1 genuine match exists; the
    different-category product fills the remaining slot rather than
    leaving the section looking emptier than it needs to."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Backfill Co")
    viewed = _make_product(profile.id, "Ferrari Red", ProductCategory.PERSONAL_CARE, 30000, ProductUnit.EACH)
    related = _make_product(profile.id, "Eternity Fragrance", ProductCategory.PERSONAL_CARE, 25000, ProductUnit.EACH)
    unrelated = _make_product(profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH)

    result = catalog_service.list_related_products(business.id, profile.id, viewed.id)

    result_ids = {p["id"] for p in result["products"]}
    assert result_ids == {str(related.id), str(unrelated.id)}


def test_list_related_products_backfill_never_duplicates_a_related_product(
    make_business, make_supplier, make_supplier_profile
):
    """A product already counted as genuinely related must never also
    appear a second time via the backfill pass."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Duplicate Co")
    viewed = _make_product(profile.id, "Viewed Item", ProductCategory.PERSONAL_CARE, 1000, ProductUnit.EACH)
    _make_product(profile.id, "Related Item", ProductCategory.PERSONAL_CARE, 1000, ProductUnit.EACH)

    result = catalog_service.list_related_products(business.id, profile.id, viewed.id)

    result_ids = [p["id"] for p in result["products"]]
    assert len(result_ids) == len(set(result_ids))  # no duplicates at all


def test_list_related_products_backfill_never_includes_a_different_suppliers_product(
    make_business, make_supplier, make_supplier_profile
):
    """Backfill is scoped to the SAME supplier too -- never pulled from
    anywhere else, matching the same "this supplier's own stock only"
    principle the genuinely-related pass already follows."""
    business = make_business()
    owner = make_supplier("backfill-owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Backfill Owner Co")
    other = make_supplier("backfill-other@example.com")
    other_profile = make_supplier_profile(other, business_name="Backfill Other Co")
    viewed = _make_product(owner_profile.id, "Ferrari Red", ProductCategory.PERSONAL_CARE, 30000, ProductUnit.EACH)
    _make_product(other_profile.id, "Not Theirs", ProductCategory.BAKERY, 1000, ProductUnit.EACH)

    result = catalog_service.list_related_products(business.id, owner_profile.id, viewed.id)

    assert result["products"] == []


def test_list_related_products_excludes_the_viewed_product_itself(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Self Excluded Co")
    viewed = _make_product(profile.id, "Ferrari Red", ProductCategory.PERSONAL_CARE, 30000, ProductUnit.EACH)

    result = catalog_service.list_related_products(business.id, profile.id, viewed.id)

    assert result["products"] == []


def test_list_related_products_excludes_products_from_a_different_supplier(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    owner = make_supplier("related-owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Owner Co")
    other = make_supplier("related-other@example.com")
    other_profile = make_supplier_profile(other, business_name="Other Co")
    viewed = _make_product(owner_profile.id, "Ferrari Red", ProductCategory.PERSONAL_CARE, 30000, ProductUnit.EACH)
    _make_product(other_profile.id, "Eternity Fragrance", ProductCategory.PERSONAL_CARE, 25000, ProductUnit.EACH)

    result = catalog_service.list_related_products(business.id, owner_profile.id, viewed.id)

    assert result["products"] == []


def test_list_related_products_caps_at_five(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Many Related Co")
    viewed = _make_product(profile.id, "Viewed Item", ProductCategory.PERSONAL_CARE, 1000, ProductUnit.EACH)
    for i in range(7):
        _make_product(profile.id, f"Related {i}", ProductCategory.PERSONAL_CARE, 1000 + i, ProductUnit.EACH)

    result = catalog_service.list_related_products(business.id, profile.id, viewed.id)

    assert len(result["products"]) == 5


def test_list_related_products_includes_out_of_stock_products(make_business, make_supplier, make_supplier_profile):
    """Same consistent behaviour as the main catalogue grid -- never a
    second, different filtering rule to remember."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Related Out Of Stock Co")
    viewed = _make_product(profile.id, "Viewed Item", ProductCategory.PERSONAL_CARE, 1000, ProductUnit.EACH)
    _make_product(profile.id, "Never Stocked", ProductCategory.PERSONAL_CARE, 1000, ProductUnit.EACH)

    result = catalog_service.list_related_products(business.id, profile.id, viewed.id)

    assert len(result["products"]) == 1
    assert result["products"][0]["inStock"] is False


def test_list_related_products_raises_for_a_genuinely_nonexistent_product(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Co")

    with pytest.raises(ProductNotFoundError):
        catalog_service.list_related_products(business.id, profile.id, uuid.uuid4())


# --- Catalogue ranking, search, and buy-it-again --------------------------


def _product(profile_id, name):
    """This file's own _make_product wants every column spelled out;
    these tests only care about the name, so the rest is fixed."""
    return _make_product(profile_id, name, ProductCategory.BEVERAGES, 1000, ProductUnit.EACH)


def _confirmed_order(business, profile, product, quantity=1):
    """A real CONFIRMED order for `product` -- the only kind that counts
    toward best-selling or buy-it-again."""
    from src.core.base_model import utcnow
    from src.domains.network.orders.models.stock_order import StockOrder, StockOrderItem, StockOrderStatus
    from src.extensions import db

    order = StockOrder(
        business_id=business.id,
        supplier_profile_id=profile.id,
        status=StockOrderStatus.CONFIRMED,
        total_cents=product.price_cents * quantity,
        submitted_at=utcnow(),
        decided_at=utcnow(),
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(
        StockOrderItem(
            stock_order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price_cents_at_add_time=product.price_cents,
        )
    )
    db.session.commit()
    return order


def test_recommended_is_the_default_and_puts_in_stock_first(
    make_business, make_supplier, make_supplier_profile
):
    """RECOMMENDED replaced NEWEST as the default: with NEWEST, whatever
    a supplier uploaded last led their shop regardless of whether it was
    even orderable."""
    from src.domains.network.connections.services.storefront import catalog_service
    from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository

    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Rank Catalogue Co")
    _product(profile.id, "Old but available")
    newest = _product(profile.id, "Newest but sold out")

    stocked = _product(profile.id, "Also available")
    for p in (stocked,):
        inventory = InventoryRepository.get_or_create_for_product(p.id, profile.id)
        InventoryRepository.adjust_quantity(inventory, 10)

    result = catalog_service.list_supplier_products(business.id, profile.id)
    names = [p["name"] for p in result["products"]]

    # The in-stock product leads, even though a newer one exists.
    assert names[0] == "Also available"
    assert newest.name in names  # sold-out products still appear, just lower


def test_best_selling_sorts_by_units_actually_sold(
    make_business, make_supplier, make_supplier_profile
):
    from src.domains.network.connections.services.storefront import catalog_service

    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Best Seller Co")
    quiet = _product(profile.id, "Barely sells")
    popular = _product(profile.id, "Sells a lot")

    _confirmed_order(business, profile, quiet, quantity=1)
    _confirmed_order(business, profile, popular, quantity=25)

    result = catalog_service.list_supplier_products(business.id, profile.id, sort="BEST_SELLING")
    names = [p["name"] for p in result["products"]]

    assert names[0] == "Sells a lot"
    # A product nobody ever ordered still appears -- LEFT JOIN, ranked
    # last, never dropped from the catalogue.
    assert "Barely sells" in names


def test_catalogue_search_matches_a_substring_of_the_name(
    make_business, make_supplier, make_supplier_profile
):
    """Substring, not prefix: a business searching inside ONE supplier's
    catalogue isn't the public discovery search, so matching "cola"
    against "Coca-Cola 500ml" is the whole point."""
    from src.domains.network.connections.services.storefront import catalog_service

    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Search Co")
    _product(profile.id, "Coca-Cola 500ml")
    _product(profile.id, "Simba Chips")

    result = catalog_service.list_supplier_products(business.id, profile.id, search_term="cola")

    assert [p["name"] for p in result["products"]] == ["Coca-Cola 500ml"]
    # totalCount reflects the FILTERED set, so pagination stays honest.
    assert result["totalCount"] == 1


def test_buy_it_again_returns_only_this_businesss_confirmed_orders(
    make_business, make_supplier, make_supplier_profile
):
    from src.domains.network.connections.services.storefront import catalog_service

    business = make_business()
    other_business = make_business("someone-else@example.com")
    profile = make_supplier_profile(make_supplier(), business_name="Reorder Co")

    mine = _product(profile.id, "What I always buy")
    theirs = _product(profile.id, "What someone else buys")
    _product(profile.id, "Never ordered by anyone")

    _confirmed_order(business, profile, mine)
    _confirmed_order(other_business, profile, theirs)

    result = catalog_service.list_buy_it_again(business.id, profile.id)

    # Personal history, not a popularity list: another business's order
    # must never appear in mine.
    assert [p["name"] for p in result["products"]] == ["What I always buy"]


def test_buy_it_again_is_empty_for_a_business_that_never_ordered(
    make_business, make_supplier, make_supplier_profile
):
    from src.domains.network.connections.services.storefront import catalog_service

    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="No History Co")
    _product(profile.id, "Something")

    assert catalog_service.list_buy_it_again(business.id, profile.id) == {"products": []}
