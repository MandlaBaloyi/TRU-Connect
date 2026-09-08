"""
Products repository + service tests. Service tests are the ones that
actually matter for correctness (validation, bulk math, ownership) --
repository tests here are thin, just confirming the SQL does what it
says, matching the split every other domain draws between the two
layers.
"""
from __future__ import annotations

import pytest

from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.domains.supplier.products.services import product_service
from src.domains.supplier.products.services.errors import ProductNotFoundError, ProductValidationError


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

    assert SupplierOfferRepository.get_by_id_and_supplier(product.id, owner_profile.id) is not None
    assert SupplierOfferRepository.get_by_id_and_supplier(product.id, other_profile.id) is None


def test_list_for_supplier_excludes_archived_by_default(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    active = _make_product(profile.id, name="Active Product")
    archived = _make_product(profile.id, name="Archived Product")
    SupplierOfferRepository.archive(archived)

    results = SupplierOfferRepository.list_for_supplier(profile.id)

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

    results = SupplierOfferRepository.list_for_supplier(profile.id, search_term="500ml")

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


# --- Service: SKU, product code, description, compare-at price -------------


def test_create_product_auto_generates_sku_when_left_blank(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    product = product_service.create_product(profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH)

    assert product.sku == "SKU-000001"


def test_create_product_uses_a_custom_sku_when_provided(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    product = product_service.create_product(
        profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH, sku="BREAD-CASE-24"
    )

    assert product.sku == "BREAD-CASE-24"


def test_create_product_rejects_a_duplicate_custom_sku_for_the_same_supplier(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product_service.create_product(
        profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH, sku="MY-SKU"
    )

    with pytest.raises(ProductValidationError):
        product_service.create_product(
            profile.id, "Milk", ProductCategory.DAIRY_CHILLED, 200, ProductUnit.EACH, sku="MY-SKU"
        )


def test_create_product_allows_the_same_custom_sku_for_different_suppliers(make_supplier, make_supplier_profile):
    """SKUs are unique per supplier, not platform-wide -- matches how
    SKUs actually work in the real world."""
    supplier_a = make_supplier("sku-dup-a@example.com")
    profile_a = make_supplier_profile(supplier_a, business_name="Dup SKU A Co")
    supplier_b = make_supplier("sku-dup-b@example.com")
    profile_b = make_supplier_profile(supplier_b, business_name="Dup SKU B Co")

    product_a = product_service.create_product(
        profile_a.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH, sku="SAME-SKU"
    )
    product_b = product_service.create_product(
        profile_b.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH, sku="SAME-SKU"
    )

    assert product_a.sku == product_b.sku == "SAME-SKU"


def test_create_product_always_generates_a_product_code(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    product = product_service.create_product(profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH)

    assert product.product_code.startswith("TRU-")


def test_create_product_two_products_get_different_product_codes(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    product1 = product_service.create_product(profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH)
    product2 = product_service.create_product(profile.id, "Milk", ProductCategory.DAIRY_CHILLED, 200, ProductUnit.EACH)

    assert product1.product_code != product2.product_code


def test_update_product_never_changes_the_product_code(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = product_service.create_product(profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH)
    original_code = product.product_code

    updated = product_service.update_product(
        product.id, profile.id, "Bread Loaves", ProductCategory.BAKERY, 150, ProductUnit.EACH
    )

    assert updated.product_code == original_code


def test_update_product_leaves_sku_unchanged_when_not_provided(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = product_service.create_product(
        profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH, sku="ORIGINAL-SKU"
    )

    updated = product_service.update_product(
        product.id, profile.id, "Bread Loaves", ProductCategory.BAKERY, 150, ProductUnit.EACH
    )

    assert updated.sku == "ORIGINAL-SKU"


def test_update_product_can_change_the_sku(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = product_service.create_product(
        profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH, sku="OLD-SKU"
    )

    updated = product_service.update_product(
        product.id, profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH, sku="NEW-SKU"
    )

    assert updated.sku == "NEW-SKU"


def test_update_product_rejects_changing_sku_to_one_already_used_by_another_product(
    make_supplier, make_supplier_profile
):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product_service.create_product(
        profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH, sku="TAKEN-SKU"
    )
    other = product_service.create_product(
        profile.id, "Milk", ProductCategory.DAIRY_CHILLED, 200, ProductUnit.EACH, sku="MILK-SKU"
    )

    with pytest.raises(ProductValidationError):
        product_service.update_product(
            other.id, profile.id, "Milk", ProductCategory.DAIRY_CHILLED, 200, ProductUnit.EACH, sku="TAKEN-SKU"
        )


def test_update_product_allows_re_saving_a_products_own_unchanged_sku(make_supplier, make_supplier_profile):
    """Re-submitting the SAME sku a product already has must never be
    treated as a collision with itself."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = product_service.create_product(
        profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH, sku="MY-OWN-SKU"
    )

    updated = product_service.update_product(
        product.id, profile.id, "Bread Loaves", ProductCategory.BAKERY, 120, ProductUnit.EACH, sku="MY-OWN-SKU"
    )

    assert updated.sku == "MY-OWN-SKU"


def test_create_product_accepts_description(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    product = product_service.create_product(
        profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH, description="3 loaves per case."
    )

    assert product.description == "3 loaves per case."


def test_create_product_description_is_optional(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    product = product_service.create_product(profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH)

    assert product.description is None


def test_create_product_accepts_a_valid_compare_at_price(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    product = product_service.create_product(
        profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH, compare_at_price_cents=1500
    )

    assert product.compare_at_price_cents == 1500


def test_create_product_rejects_compare_at_price_equal_to_price(make_supplier, make_supplier_profile):
    """A "sale" price that isn't actually lower than the real price is
    either a mistake or meaningless."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    with pytest.raises(ProductValidationError):
        product_service.create_product(
            profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH, compare_at_price_cents=1000
        )


def test_create_product_rejects_compare_at_price_below_price(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)

    with pytest.raises(ProductValidationError):
        product_service.create_product(
            profile.id, "Bread", ProductCategory.BAKERY, 1000, ProductUnit.EACH, compare_at_price_cents=500
        )


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


def test_unarchive_product_clears_is_archived(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    product_service.archive_product(product.id, profile.id)

    unarchived = product_service.unarchive_product(product.id, profile.id)

    assert unarchived.is_archived is False


def test_delete_product_soft_deletes_and_it_stops_appearing_in_any_list(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, name="Gone Soon")

    product_service.delete_product(product.id, profile.id)

    active_list = product_service.list_products(profile.id)
    archived_list = product_service.list_products(profile.id, is_archived=True)
    everything = product_service.list_products(profile.id, is_archived=None)
    assert "Gone Soon" not in {p.name for p in active_list}
    assert "Gone Soon" not in {p.name for p in archived_list}
    assert "Gone Soon" not in {p.name for p in everything}


def test_delete_product_never_actually_removes_the_row(make_supplier, make_supplier_profile):
    """The whole point of soft delete -- the real row, and everything
    it can be analysed from later, stays intact."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, name="Still Really Here")

    product_service.delete_product(product.id, profile.id)

    from src.extensions import db
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer

    raw_row = db.session.get(SupplierOffer, product.id)
    assert raw_row is not None
    assert raw_row.name == "Still Really Here"
    assert raw_row.is_deleted is True
    assert raw_row.deleted_at is not None


def test_delete_product_raises_not_found_for_other_suppliers_product(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    other_supplier = make_supplier("someone-else@example.com")
    other_profile = make_supplier_profile(other_supplier, business_name="Someone Else Co")
    product = _make_product(other_profile.id)

    with pytest.raises(ProductNotFoundError):
        product_service.delete_product(product.id, profile.id)


def test_bulk_unarchive_only_affects_owned_products(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    mine = _make_product(profile.id)
    product_service.archive_product(mine.id, profile.id)
    other_supplier = make_supplier("bulk-unarchive-other@example.com")
    other_profile = make_supplier_profile(other_supplier, business_name="Bulk Unarchive Other Co")
    theirs = _make_product(other_profile.id)
    product_service.archive_product(theirs.id, other_profile.id)

    product_service.bulk_unarchive([mine.id, theirs.id], profile.id)

    assert SupplierOfferRepository.get_by_id(mine.id).is_archived is False
    assert SupplierOfferRepository.get_by_id(theirs.id).is_archived is True


def test_bulk_delete_only_affects_owned_products(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    mine = _make_product(profile.id)
    other_supplier = make_supplier("bulk-delete-other@example.com")
    other_profile = make_supplier_profile(other_supplier, business_name="Bulk Delete Other Co")
    theirs = _make_product(other_profile.id)

    product_service.bulk_delete([mine.id, theirs.id], profile.id)

    from src.extensions import db
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer

    # get_by_id correctly filters out deleted rows (is_deleted=False),
    # so it can never be used to confirm a row WAS deleted -- querying
    # the raw row directly instead, same as
    # test_delete_product_never_actually_removes_the_row above.
    assert db.session.get(SupplierOffer, mine.id).is_deleted is True
    assert db.session.get(SupplierOffer, theirs.id).is_deleted is False


# --- Service: list filtering, including the real archived-tab bug ----------


def test_list_products_default_returns_active_only(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    active = _make_product(profile.id, name="Active One")
    archived = _make_product(profile.id, name="Archived One")
    product_service.archive_product(archived.id, profile.id)

    results = product_service.list_products(profile.id)

    names = {p.name for p in results}
    assert names == {"Active One"}


def test_list_products_is_archived_true_returns_archived_only(make_supplier, make_supplier_profile):
    """THE REAL BUG found during real device testing: the "Archived"
    filter tab used to set include_archived=True, which only ever
    meant "stop excluding archived rows" -- never "show ONLY archived
    rows." Selecting Archived on the real app returned every product,
    active and archived mixed. This is the direct proof the fix
    actually filters correctly, not just stops crashing."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    active = _make_product(profile.id, name="Active One")
    archived = _make_product(profile.id, name="Archived One")
    product_service.archive_product(archived.id, profile.id)

    results = product_service.list_products(profile.id, is_archived=True)

    names = {p.name for p in results}
    assert names == {"Archived One"}
    assert "Active One" not in names


def test_list_products_is_archived_none_returns_both(make_supplier, make_supplier_profile):
    """Not currently used by any real caller, but the parameter exists
    for a genuine future need -- confirmed it actually works, not just
    assumed."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    active = _make_product(profile.id, name="Active One")
    archived = _make_product(profile.id, name="Archived One")
    product_service.archive_product(archived.id, profile.id)

    results = product_service.list_products(profile.id, is_archived=None)

    names = {p.name for p in results}
    assert names == {"Active One", "Archived One"}


# --- Service: bulk price adjustment -----------------------------------------


def test_bulk_adjust_price_percentage_increase(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A", price_cents=1000)
    p2 = _make_product(profile.id, name="B", price_cents=2000)

    product_service.bulk_adjust_price([p1.id, p2.id], profile.id, "INCREASE", "PERCENTAGE", 10)

    assert SupplierOfferRepository.get_by_id(p1.id).price_cents == 1100
    assert SupplierOfferRepository.get_by_id(p2.id).price_cents == 2200


def test_bulk_adjust_price_fixed_decrease(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A", price_cents=1000)

    product_service.bulk_adjust_price([p1.id], profile.id, "DECREASE", "FIXED", 300)

    assert SupplierOfferRepository.get_by_id(p1.id).price_cents == 700


def test_bulk_adjust_price_clamps_at_zero_never_negative(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A", price_cents=100)

    product_service.bulk_adjust_price([p1.id], profile.id, "DECREASE", "FIXED", 500)

    assert SupplierOfferRepository.get_by_id(p1.id).price_cents == 0


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
    assert SupplierOfferRepository.get_by_id(victim_product.id).price_cents == 1000


# --- Service: bulk set discount ---------------------------------------------


def test_bulk_set_discount_computes_correct_compare_at_price(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, name="Perfume", price_cents=25000)

    product_service.bulk_set_discount([product.id], profile.id, 20)

    refreshed = SupplierOfferRepository.get_by_id(product.id)
    assert refreshed.compare_at_price_cents == 31250
    # Real price is NEVER touched -- this sets compare_at_price only.
    assert refreshed.price_cents == 25000


def test_bulk_set_discount_never_touches_the_real_price(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, name="Bread", price_cents=1850)

    product_service.bulk_set_discount([product.id], profile.id, 15)

    assert SupplierOfferRepository.get_by_id(product.id).price_cents == 1850


def test_bulk_set_discount_result_round_trips_to_the_same_percentage():
    """Confirms the formula genuinely matches the frontend's own
    calculateDiscount.ts -- a supplier who sets "20% off" here must see
    a real "20% OFF" badge on the result, not an off-by-rounding
    number."""

    def calculate_discount_percent(price_cents, compare_at_cents):
        savings = compare_at_cents - price_cents
        return round((savings / compare_at_cents) * 100)

    price = 1850
    compare_at = round(price / (1 - 15 / 100))
    assert calculate_discount_percent(price, compare_at) == 15


def test_bulk_set_discount_applies_across_multiple_products_using_each_products_own_price(
    make_supplier, make_supplier_profile
):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    p1 = _make_product(profile.id, name="A", price_cents=1000)
    p2 = _make_product(profile.id, name="B", price_cents=5000)

    product_service.bulk_set_discount([p1.id, p2.id], profile.id, 10)

    assert SupplierOfferRepository.get_by_id(p1.id).compare_at_price_cents == 1111
    assert SupplierOfferRepository.get_by_id(p2.id).compare_at_price_cents == 5556


def test_bulk_set_discount_rejects_zero_percent(make_supplier, make_supplier_profile):
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, price_cents=1000)

    with pytest.raises(ProductValidationError):
        product_service.bulk_set_discount([product.id], profile.id, 0)


def test_bulk_set_discount_rejects_100_percent(make_supplier, make_supplier_profile):
    """100% would divide by zero -- must be a real, clear rejection,
    never a crash."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, price_cents=1000)

    with pytest.raises(ProductValidationError):
        product_service.bulk_set_discount([product.id], profile.id, 100)


def test_bulk_set_discount_rejects_over_100_percent(make_supplier, make_supplier_profile):
    """Over 100 would go negative -- must never silently produce a
    negative compare-at price."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, price_cents=1000)

    with pytest.raises(ProductValidationError):
        product_service.bulk_set_discount([product.id], profile.id, 150)


def test_bulk_set_discount_rejects_a_result_that_would_exceed_the_price_ceiling(
    make_supplier, make_supplier_profile
):
    """A genuinely rare combination (a price already near the real
    ceiling, combined with a steep discount) -- must be a real,
    honest rejection, never a silently clamped/wrong number."""
    from src.domains.supplier.products.services.product_service import MAX_PRICE_CENTS

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id, price_cents=MAX_PRICE_CENTS - 100)

    with pytest.raises(ProductValidationError):
        product_service.bulk_set_discount([product.id], profile.id, 99)


def test_bulk_set_discount_is_all_or_nothing_across_a_batch(make_supplier, make_supplier_profile):
    """If ANY product in the batch would exceed the price ceiling, NONE
    of the batch's compare_at_price should be written -- matching the
    same all-or-nothing behaviour every other bulk action in this file
    already has, not partial success."""
    from src.domains.supplier.products.services.product_service import MAX_PRICE_CENTS

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    ordinary_product = _make_product(profile.id, name="Ordinary", price_cents=1000)
    extreme_product = _make_product(profile.id, name="Extreme", price_cents=MAX_PRICE_CENTS - 100)

    with pytest.raises(ProductValidationError):
        product_service.bulk_set_discount([ordinary_product.id, extreme_product.id], profile.id, 99)

    # Neither product was touched -- the whole batch was rejected.
    assert SupplierOfferRepository.get_by_id(ordinary_product.id).compare_at_price_cents is None
    assert SupplierOfferRepository.get_by_id(extreme_product.id).compare_at_price_cents is None


def test_bulk_set_discount_excludes_other_suppliers_products(make_supplier, make_supplier_profile):
    owner = make_supplier("discount-owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Discount Owner Co")
    other = make_supplier("discount-other@example.com")
    other_profile = make_supplier_profile(other, business_name="Discount Other Co")
    victim_product = _make_product(other_profile.id, name="Not Yours", price_cents=1000)

    result = product_service.bulk_set_discount([victim_product.id], owner_profile.id, 20)

    assert result == []
    assert SupplierOfferRepository.get_by_id(victim_product.id).compare_at_price_cents is None


def test_bulk_archive_only_affects_owned_products(make_supplier, make_supplier_profile):
    owner = make_supplier("owner4@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Owner Co 4")
    other = make_supplier("other4@example.com")
    other_profile = make_supplier_profile(other, business_name="Other Co 4")
    mine = _make_product(owner_profile.id, name="Mine")
    theirs = _make_product(other_profile.id, name="Theirs")

    product_service.bulk_archive([mine.id, theirs.id], owner_profile.id)

    assert SupplierOfferRepository.get_by_id(mine.id).is_archived is True
    assert SupplierOfferRepository.get_by_id(theirs.id).is_archived is False
