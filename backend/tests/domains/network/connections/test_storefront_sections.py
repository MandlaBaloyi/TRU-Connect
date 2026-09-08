"""
The merchandised storefront sections on a supplier's brand profile --
GET /suppliers/{id}/storefront.

Distinct from test_profile_products.py, which covers the same
supplier's catalogue grouped by CATEGORY. That answers "here is
everything"; this answers "here is what to look at first".
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.extensions import db


def _auth(user, role: str = "business") -> dict:
    token = create_access_token(identity=str(user.id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def _make_product(
    profile_id,
    name,
    *,
    price_cents=1200,
    compare_at_price_cents=None,
    unit_quantity=None,
    selling_unit=ProductUnit.EACH,
    created_at=None,
):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    product = SupplierOfferRepository.create(
        supplier_profile_id=profile_id,
        name=name,
        category=ProductCategory.BEVERAGES,
        price_cents=price_cents,
        selling_unit=selling_unit,
        sku=generate_sku(profile_id),
        product_code=generate_product_code(),
        unit_quantity=unit_quantity,
        unit_measure=ProductUnit.BOTTLE if unit_quantity else None,
        compare_at_price_cents=compare_at_price_cents,
    )
    if created_at is not None:
        product.created_at = created_at
        db.session.commit()
    return product


def _storefront(client, business, profile_id):
    resp = client.get(
        f"/api/v1/supplier-discovery/suppliers/{profile_id}/storefront", headers=_auth(business)
    )
    assert resp.status_code == 200
    return resp.get_json()["data"]["sections"]


def _section(sections, section_type):
    return next((s for s in sections if s["type"] == section_type), None)


def test_a_supplier_who_configured_nothing_still_gets_a_storefront(
    client, make_business, make_supplier, make_supplier_profile
):
    """THE DEFAULT PATH, and the one almost every supplier is on. No
    configuration rows exist, so the service falls back to its default
    section set -- and must do so WITHOUT writing anything, since a
    business browsing a profile must never create rows in that
    supplier's own account."""
    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Default Storefront Co")
    for index in range(4):
        _make_product(profile.id, f"Sale item {index}", price_cents=1000, compare_at_price_cents=2000)

    sections = _storefront(client, business, profile.id)

    assert _section(sections, "ON_SALE") is not None
    # Nothing was persisted on read.
    from src.domains.supplier.supplier_profile.models.supplier_storefront import (
        SupplierStorefrontSection,
    )

    assert SupplierStorefrontSection.query.filter_by(supplier_profile_id=profile.id).count() == 0


def test_on_sale_only_holds_genuinely_reduced_products(
    client, make_business, make_supplier, make_supplier_profile
):
    """A compare-at price at or BELOW the price is stale or
    mis-entered data, never a saving -- showing it would put a discount
    on a product that has none."""
    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Real Discounts Co")

    for index in range(3):
        _make_product(profile.id, f"Real sale {index}", price_cents=1000, compare_at_price_cents=1500)
    # Not a discount: compare-at equals the price.
    _make_product(profile.id, "Not on sale", price_cents=1000, compare_at_price_cents=1000)
    # Not a discount: compare-at is LOWER than the price.
    _make_product(profile.id, "Backwards", price_cents=2000, compare_at_price_cents=1000)

    section = _section(_storefront(client, business, profile.id), "ON_SALE")

    names = [p["name"] for p in section["products"]]
    assert len(names) == 3
    assert "Not on sale" not in names
    assert "Backwards" not in names


def test_bulk_value_excludes_single_unit_products_and_sorts_by_per_unit_price(
    client, make_business, make_supplier, make_supplier_profile
):
    """A product sold as Each has no per-unit price to compute -- price
    divided by one is just the price -- so putting it in a strip titled
    "better per unit in bulk" would claim a saving that does not
    exist."""
    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Bulk Co")

    _make_product(profile.id, "Case of 24", price_cents=24_000, unit_quantity=24)   # R10.00 each
    _make_product(profile.id, "Case of 6", price_cents=12_000, unit_quantity=6)     # R20.00 each
    _make_product(profile.id, "Case of 12", price_cents=18_000, unit_quantity=12)   # R15.00 each
    _make_product(profile.id, "Single item", price_cents=5_000)                      # no unit_quantity
    _make_product(profile.id, "Pack of one", price_cents=5_000, unit_quantity=1)     # quantity 1

    section = _section(_storefront(client, business, profile.id), "BULK_VALUE")

    names = [p["name"] for p in section["products"]]
    assert names == ["Case of 24", "Case of 12", "Case of 6"], "cheapest per unit first"
    assert "Single item" not in names
    assert "Pack of one" not in names


def test_just_added_is_windowed_not_merely_sorted(
    client, make_business, make_supplier, make_supplier_profile
):
    """THE WHOLE CLAIM OF THIS SECTION IS RECENCY. Ordering by
    created_at alone would hand the newest products to a supplier whose
    last upload was eight months ago and label them new -- the section
    is meant to disappear for a supplier who has added nothing lately,
    and the window is what makes it disappear."""
    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Stale Catalogue Co")

    long_ago = datetime.now(timezone.utc) - timedelta(days=200)
    for index in range(4):
        _make_product(profile.id, f"Old item {index}", created_at=long_ago)

    sections = _storefront(client, business, profile.id)
    assert _section(sections, "NEW_ARRIVALS") is None, "nothing added recently, so no new-arrivals strip"

    # Add three fresh ones and the section appears.
    for index in range(3):
        _make_product(profile.id, f"Fresh item {index}")

    section = _section(_storefront(client, business, profile.id), "NEW_ARRIVALS")
    assert section is not None
    assert all(p["name"].startswith("Fresh") for p in section["products"])


def test_a_thin_section_does_not_appear_at_all(
    client, make_business, make_supplier, make_supplier_profile
):
    """A strip with one product reads as a broken shelf rather than a
    short one -- and a new supplier, who has the least of everything,
    is exactly who would otherwise see the most of them."""
    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Thin Co")
    _make_product(profile.id, "Lonely sale item", price_cents=1000, compare_at_price_cents=2000)

    assert _section(_storefront(client, business, profile.id), "ON_SALE") is None


def test_archived_products_never_reach_the_storefront(
    client, make_business, make_supplier, make_supplier_profile
):
    """Archived is gone. Out of stock is NOT -- see the repository's own
    note on why that asymmetry is deliberate."""
    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Archive Co")

    for index in range(3):
        _make_product(profile.id, f"Live sale {index}", price_cents=1000, compare_at_price_cents=2000)
    archived = _make_product(profile.id, "Archived sale", price_cents=1000, compare_at_price_cents=2000)
    archived.is_archived = True
    db.session.commit()

    section = _section(_storefront(client, business, profile.id), "ON_SALE")
    assert "Archived sale" not in [p["name"] for p in section["products"]]


def test_storefront_is_browsable_without_a_connection(
    client, make_business, make_supplier, make_supplier_profile
):
    """Browsing stays open across this whole package -- only ORDERING
    is gated. A business deciding whether to connect at all has to be
    able to see what the supplier sells first."""
    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Unconnected Co")
    for index in range(3):
        _make_product(profile.id, f"Sale {index}", price_cents=1000, compare_at_price_cents=2000)

    # No connection of any kind is created.
    sections = _storefront(client, business, profile.id)
    assert _section(sections, "ON_SALE") is not None


def test_a_supplier_can_disable_a_section(
    client, make_business, make_supplier, make_supplier_profile
):
    """The toggle is the supplier's, and it is what the whole
    configuration table exists for.

    THIS TEST CAUGHT A REAL BUG. The service originally loaded only the
    ENABLED rows and fell back to defaults when that list came back
    empty -- so a supplier who switched their one configured section
    OFF was indistinguishable from a supplier who had never configured
    anything, and the defaults put the section they had just disabled
    straight back onto their profile. Switching something off has to
    mean it stays off."""
    from src.domains.supplier.supplier_profile.models.supplier_storefront import (
        StorefrontSectionType,
        SupplierStorefrontSection,
    )

    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Opted Out Co")
    for index in range(3):
        _make_product(profile.id, f"Sale {index}", price_cents=1000, compare_at_price_cents=2000)

    # Configure explicitly: best sellers on, on-sale off.
    db.session.add(
        SupplierStorefrontSection(
            supplier_profile_id=profile.id,
            section_type=StorefrontSectionType.ON_SALE,
            is_enabled=False,
            position=0,
        )
    )
    db.session.commit()

    sections = _storefront(client, business, profile.id)
    assert _section(sections, "ON_SALE") is None, "a disabled section must not come back via the defaults"


def test_supplier_order_decides_section_order(
    client, make_business, make_supplier, make_supplier_profile
):
    """ORDER IS DATA, NOT CODE -- the reason a wholesaler can put their
    promoted range above the fold without an app release."""
    from src.domains.supplier.supplier_profile.models.supplier_storefront import (
        StorefrontSectionType,
        SupplierStorefrontSection,
    )

    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Ordered Co")
    for index in range(3):
        _make_product(
            profile.id, f"Both {index}", price_cents=1000, compare_at_price_cents=2000, unit_quantity=6
        )

    # Bulk deliberately placed BEFORE on-sale, the opposite of the
    # default order.
    db.session.add_all(
        [
            SupplierStorefrontSection(
                supplier_profile_id=profile.id,
                section_type=StorefrontSectionType.BULK_VALUE,
                position=0,
            ),
            SupplierStorefrontSection(
                supplier_profile_id=profile.id,
                section_type=StorefrontSectionType.ON_SALE,
                position=1,
            ),
        ]
    )
    db.session.commit()

    types = [s["type"] for s in _storefront(client, business, profile.id)]
    assert types == ["BULK_VALUE", "ON_SALE"]
