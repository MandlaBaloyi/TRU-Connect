"""
V2 step 2: the catalogue exists, and nothing depends on it yet.

THE POINT OF THESE TESTS IS THE DORMANCY CLAIM. Step 2's whole safety
argument is "an unmatched offer behaves exactly as it did before", and
an argument nobody checks is a hope. So the first test creates an offer
the ordinary way and asserts the new column is null and harmless, rather
than testing that the catalogue works.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from src.domains.catalogue.products.models.brand import Brand
from src.domains.catalogue.products.models.product import Product
from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
from src.domains.supplier.products.models.supplier_offer import SupplierOffer
from src.extensions import db


def _offer(supplier_profile_id, **overrides):
    """An offer built the way the rest of the app builds one -- with no
    mention of the catalogue anywhere."""
    values = dict(
        supplier_profile_id=supplier_profile_id,
        name="Sunlight Dishwashing Liquid",
        category=ProductCategory.HOUSEHOLD_CLEANING,
        price_cents=4599,
        selling_unit=ProductUnit.EACH,
        sku=f"SKU-{uuid.uuid4().hex[:8]}",
        product_code=uuid.uuid4().hex[:10].upper(),
    )
    values.update(overrides)
    return SupplierOffer(**values)


def test_an_offer_created_the_old_way_is_simply_unmatched(db_session, make_supplier, make_supplier_profile):
    """The dormancy claim, checked rather than asserted.

    Nothing in the application sets product_id yet. An offer created
    without any knowledge that a catalogue exists must save cleanly and
    come back unmatched -- if this ever fails, step 2 stopped being
    additive and the catalogue became a requirement."""
    profile = make_supplier_profile(make_supplier())
    offer = _offer(profile.id)
    db_session.add(offer)
    db_session.commit()

    assert offer.product_id is None


def test_an_offer_can_be_matched_to_a_catalogue_product(db_session, make_supplier, make_supplier_profile):
    profile = make_supplier_profile(make_supplier())
    brand = Brand(name="Sunlight", slug="sunlight")
    db_session.add(brand)
    db_session.flush()

    product = Product(
        name="Sunlight Dishwashing Liquid 750ml",
        normalized_name="sunlightdishwashingliquid750ml",
        brand_id=brand.id,
        category=ProductCategory.HOUSEHOLD_CLEANING,
        unit_quantity=750,
        unit_measure=ProductUnit.ML,
        gtin="6001087001234",
    )
    db_session.add(product)
    db_session.flush()

    offer = _offer(profile.id, product_id=product.id)
    db_session.add(offer)
    db_session.commit()

    assert offer.product_id == product.id


def test_two_suppliers_can_offer_the_same_product(db_session, make_supplier, make_supplier_profile):
    """The reason the split exists at all.

    Under v1 these were two unrelated rows and no question could be
    asked across them. Sharing one product id is what later makes
    "who sells this cheaper" answerable."""
    profile = make_supplier_profile(make_supplier('a@example.com'), business_name='A Co')
    other = make_supplier_profile(make_supplier('b@example.com'), business_name='B Co')

    product = Product(
        name="Coca-Cola Original 2L",
        normalized_name="cocacolaoriginal2l",
        category=ProductCategory.BEVERAGES,
        unit_quantity=2,
        unit_measure=ProductUnit.L,
    )
    db_session.add(product)
    db_session.flush()

    cheap = _offer(profile.id, product_id=product.id, price_cents=2199)
    dear = _offer(other.id, product_id=product.id, price_cents=2650)
    db_session.add_all([cheap, dear])
    db_session.commit()

    both = SupplierOffer.query.filter_by(product_id=product.id).all()
    assert len(both) == 2
    assert {o.supplier_profile_id for o in both} == {profile.id, other.id}


def test_a_barcode_cannot_be_catalogued_twice(db_session):
    """Two rows sharing a GTIN means the catalogue is already wrong, and
    a duplicate is precisely what makes a price comparison a lie."""
    first = Product(
        name="Koo Baked Beans 410g",
        normalized_name="koobakedbeans410g",
        category=ProductCategory.FOOD_GROCERY,
        gtin="6001275000123",
    )
    db_session.add(first)
    db_session.commit()

    db_session.add(
        Product(
            name="KOO Baked Beans in Tomato Sauce 410g",
            normalized_name="koobakedbeansintomatosauce410g",
            category=ProductCategory.FOOD_GROCERY,
            gtin="6001275000123",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_products_without_a_barcode_are_allowed_and_are_not_duplicates(db_session):
    """Refusing barcodeless products would make the catalogue useless
    for exactly the informal-trade goods this platform exists to serve,
    and NULLs must not collide with each other under the unique index."""
    for name in ("Loose Potatoes 10kg", "Building Sand 50kg"):
        db_session.add(
            Product(
                name=name,
                normalized_name=name.lower().replace(" ", ""),
                category=ProductCategory.OTHER,
            )
        )
    db_session.commit()

    assert Product.query.filter(Product.gtin.is_(None)).count() == 2


def test_deleting_a_catalogue_product_unmatches_offers_instead_of_deleting_them(
    db_session, make_supplier, make_supplier_profile
):
    """SET NULL, not CASCADE.

    A catalogue correction must never destroy a supplier's offer or the
    order history hanging off it. The honest outcome is the offer
    falling back to unmatched."""
    profile = make_supplier_profile(make_supplier())
    product = Product(
        name="Iwisa Maize Meal 5kg",
        normalized_name="iwisamaizemeal5kg",
        category=ProductCategory.FOOD_GROCERY,
    )
    db_session.add(product)
    db_session.flush()

    offer = _offer(profile.id, product_id=product.id)
    db_session.add(offer)
    db_session.commit()
    offer_id = offer.id

    db_session.execute(
        db.text("DELETE FROM catalogue.products WHERE id = :pid"), {"pid": str(product.id)}
    )
    db_session.commit()
    db_session.expire_all()

    survivor = db.session.get(SupplierOffer, offer_id)
    assert survivor is not None, "deleting a catalogue product must not delete the offer"
    assert survivor.product_id is None
