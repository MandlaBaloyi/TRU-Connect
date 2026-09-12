"""
Where did this number come from? (V2_13 §3.3)

THE QUESTION THIS ANSWERS, and it has no answer without the column: a
supplier edits a price in the app at 09:00 and their ERP pushes the
old one at 09:05. Which is correct? At tier 3 the ERP is usually
authoritative and the app is usually a convenience -- but "usually" is
a policy, and a policy needs a field to act on.

WHY THE TESTS ARE ABOUT DISTINGUISHABILITY rather than about any
individual value. The column is only worth having if two channels
writing the same row end up looking different afterwards; a default
that quietly applied to everything would pass a naive "is it set?"
test and be worthless.

NOTHING WRITES API YET. The inbound API exists but no ERP uses it, so
that value is exercised here only as a shape check -- proof the
vocabulary is complete rather than proof a caller passes it.
"""
from __future__ import annotations

import pytest

from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
from src.domains.supplier.inventory.services import inventory_service
from src.domains.supplier.products.services import product_service
from src.shared.constants.write_source import WriteSource


@pytest.fixture()
def profile(make_supplier, make_supplier_profile):
    return make_supplier_profile(make_supplier())


def _create(profile, name="Sugar 2.5kg", **kwargs):
    return product_service.create_product(
        supplier_profile_id=profile.id,
        name=name,
        category=ProductCategory.FOOD_GROCERY,
        price_cents=4500,
        selling_unit=ProductUnit.EACH,
        **kwargs,
    )


class TestOffers:
    def test_the_app_is_the_default(self, app, db_session, profile):
        """Every row that existed before this column did was written by
        a person in the app, because no other channel could write one.
        APP is the honest default, not a placeholder."""
        product = _create(profile)

        assert product.source == WriteSource.APP

    def test_an_import_is_distinguishable_from_a_typed_row(self, app, db_session, profile):
        """THE WHOLE POINT. If both looked the same afterwards the
        column would be decoration."""
        typed = _create(profile, name="Typed By Hand")
        imported = _create(profile, name="From A Spreadsheet", source=WriteSource.IMPORT)

        assert typed.source == WriteSource.APP
        assert imported.source == WriteSource.IMPORT

    def test_editing_in_the_app_takes_ownership_of_an_imported_row(
        self, app, db_session, profile
    ):
        """`source` answers "who wrote the value that is in this row
        NOW". An offer imported in January and hand-corrected in March
        is an APP row -- the correction is precisely the thing a later
        conflict has to reason about, and treating it as still-imported
        would let an ERP silently revert a deliberate human fix.
        """
        product = _create(profile, name="Imported Then Fixed", source=WriteSource.IMPORT)
        assert product.source == WriteSource.IMPORT

        product_service.update_product(
            product_id=product.id,
            supplier_profile_id=profile.id,
            name="Imported Then Fixed",
            category=ProductCategory.FOOD_GROCERY,
            price_cents=5200,
            selling_unit=ProductUnit.EACH,
        )

        assert product.source == WriteSource.APP


class TestInventory:
    def test_stock_records_its_channel(self, app, db_session, profile):
        """A supplier typing a stock count and an ERP pushing one are
        different claims about the same number -- only the first is
        somebody standing in the warehouse looking at a shelf."""
        product = _create(profile)

        inventory_service.adjust_stock(
            product_id=product.id,
            supplier_profile_id=profile.id,
            quantity_delta=40,
            reason="STOCK_RECEIVED",
            source=WriteSource.IMPORT,
        )

        from src.domains.supplier.inventory.repositories.inventory_repository import (
            InventoryRepository,
        )

        inventory = InventoryRepository.get_or_create_for_product(product.id, profile.id)
        assert inventory.source == WriteSource.IMPORT

    def test_a_later_app_adjustment_takes_the_row_back(self, app, db_session, profile):
        product = _create(profile)
        for source in (WriteSource.IMPORT, WriteSource.APP):
            inventory_service.adjust_stock(
                product_id=product.id,
                supplier_profile_id=profile.id,
                quantity_delta=5,
                reason="STOCK_RECEIVED",
                source=source,
            )

        from src.domains.supplier.inventory.repositories.inventory_repository import (
            InventoryRepository,
        )

        inventory = InventoryRepository.get_or_create_for_product(product.id, profile.id)
        assert inventory.source == WriteSource.APP
        assert inventory.quantity_on_hand == 10


def test_the_vocabulary_is_complete():
    """Three channels, and API exists before anything writes it -- so
    the day an ERP arrives, the value it needs is already in the enum
    and already in the database type."""
    assert {s.value for s in WriteSource} == {"APP", "IMPORT", "API"}
