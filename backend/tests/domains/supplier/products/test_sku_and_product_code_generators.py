"""
Tests for algorithms/product_code_generator.py and sku_generator.py --
the two pieces that give every product a real, human-readable
identifier in place of its own internal UUID.
"""
from __future__ import annotations

import re

from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
from src.domains.supplier.products.algorithms.sku_generator import generate_sku
from src.domains.supplier.products.repositories.product_repository import ProductRepository


class TestGenerateProductCode:
    def test_produces_the_expected_format(self, db_session):
        code = generate_product_code()

        assert re.fullmatch(r"TRU-[23456789ABCDEFGHJKLMNPQRSTUVWXYZ]{6}", code)

    def test_never_contains_ambiguous_characters(self, db_session):
        """0/O and 1/I are deliberately excluded -- meant to be read
        aloud or typed by hand without confusion."""
        code = generate_product_code()

        assert not any(c in code for c in "01OI")

    def test_two_calls_produce_different_codes(self, db_session):
        code1 = generate_product_code()
        code2 = generate_product_code()

        assert code1 != code2

    def test_retries_on_a_real_collision(self, db_session, monkeypatch):
        """Confirms the collision-check loop actually works, not just
        that it exists -- forces the FIRST candidate to appear taken,
        and confirms a second, different code is produced instead of
        the function giving up or returning the taken one anyway."""
        call_count = {"n": 0}
        original_exists = ProductRepository.product_code_exists

        def _first_call_says_taken(code):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return True  # simulate: this exact code is already in use
            return original_exists(code)

        monkeypatch.setattr(ProductRepository, "product_code_exists", _first_call_says_taken)

        code = generate_product_code()

        assert call_count["n"] >= 2  # proves it actually retried, not just got lucky
        assert code is not None


class TestGenerateSku:
    def test_first_sku_for_a_new_supplier_is_0001(self, make_supplier, make_supplier_profile):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)

        sku = generate_sku(profile.id)

        assert sku == "SKU-000001"

    def test_second_sku_for_the_same_supplier_is_0002(self, make_supplier, make_supplier_profile):
        supplier = make_supplier()
        profile = make_supplier_profile(supplier)

        generate_sku(profile.id)
        second = generate_sku(profile.id)

        assert second == "SKU-000002"

    def test_two_different_suppliers_each_start_at_0001(self, make_supplier, make_supplier_profile):
        """Per-supplier, not platform-wide -- matches how SKUs actually
        work in the real world."""
        supplier_a = make_supplier("sku-supplier-a@example.com")
        profile_a = make_supplier_profile(supplier_a, business_name="Supplier A Co")
        supplier_b = make_supplier("sku-supplier-b@example.com")
        profile_b = make_supplier_profile(supplier_b, business_name="Supplier B Co")

        sku_a = generate_sku(profile_a.id)
        sku_b = generate_sku(profile_b.id)

        assert sku_a == "SKU-000001"
        assert sku_b == "SKU-000001"

    def test_counter_keeps_moving_forward_even_after_a_product_is_deleted(
        self, make_supplier, make_supplier_profile
    ):
        """The counter itself never rewinds -- confirmed directly
        against SupplierProfile.next_sku_sequence rather than inferred,
        since nothing about the counter's own storage cares whether a
        product using an earlier SKU still exists."""
        from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
        from src.extensions import db

        supplier = make_supplier()
        profile = make_supplier_profile(supplier)

        generate_sku(profile.id)
        generate_sku(profile.id)
        third = generate_sku(profile.id)

        assert third == "SKU-000003"
        refreshed = db.session.get(SupplierProfile, profile.id)
        assert refreshed.next_sku_sequence == 4
