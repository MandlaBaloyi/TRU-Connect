"""
A supplier's spreadsheet, end to end, into the catalogue.

THIS IS THE TEST THE WHOLE OF STEP 6 WAS FOR. Everything before it built
pieces: a matcher nothing called, a catalogue nothing filled, four CSV
columns nothing read. This proves the chain actually connects -- upload
a file, and products end up matched to a shared catalogue.

ENTIRELY FREE. No key, no network, no model. MATCHING_MODE defaults to
deterministic and every tier exercised here is barcode, alias,
normalised or rules.

THE SECOND SUPPLIER IS THE POINT. One supplier's import creating
catalogue rows is bookkeeping. A SECOND supplier's completely
differently-worded file landing on those same rows is the thing that
makes "who sells this cheaper" answerable, and it is what the tests
below actually assert.
"""
from __future__ import annotations

import pytest

from src.domains.catalogue.matching.models.match_review import MatchReview, ReviewStatus
from src.domains.catalogue.products.models.product import Product
from src.domains.supplier.bulk_import.repositories.import_job_repository import (
    ImportJobRepository,
)
from src.domains.supplier.bulk_import.workers.import_worker import run_import
from src.domains.supplier.products.repositories.supplier_offer_repository import (
    SupplierOfferRepository,
)


def _run(profile_id, filename: str, payload: bytes):
    job = ImportJobRepository.create(profile_id, filename, False)
    run_import(job.id, profile_id, filename, payload, None, None)
    return job


# 5449000054227 is Coca-Cola's real EAN-13. 6001087001236 is an
# invented SA-prefix code whose CHECK DIGIT IS CORRECT -- it used to
# end in 4, which is not a valid GTIN, and the barcode tier now
# refuses those (see algorithms/gtin.py). A fixture that is not a
# real barcode has to at least be an arithmetically possible one.
WITH_BARCODES = (
    b"name,category,price,unit,sku,barcode,brand,pack_quantity,pack_unit\n"
    b"Coca-Cola Original 2L,Beverages,22.00,Each,CC2L,5449000054227,Coca-Cola,2,L\n"
    b"Sunlight Dishwashing 750ml,Household & Cleaning,34.99,Each,SL750,6001087001236,Sunlight,750,ml\n"
)


def test_an_import_fills_the_catalogue(make_supplier, make_supplier_profile):
    """Nobody types a product catalogue. It accumulates as suppliers
    join -- the first supplier to send a product creates its entry."""
    profile = make_supplier_profile(make_supplier())

    _run(profile.id, "week1.csv", WITH_BARCODES)

    products = Product.query.all()
    assert len(products) == 2
    assert {p.name for p in products} == {
        "Coca-Cola Original 2L",
        "Sunlight Dishwashing 750ml",
    }
    assert {p.gtin for p in products} == {"5449000054227", "6001087001236"}


def test_every_offer_ends_up_linked_to_a_catalogue_product(
    make_supplier, make_supplier_profile
):
    profile = make_supplier_profile(make_supplier())
    _run(profile.id, "week1.csv", WITH_BARCODES)

    offers = SupplierOfferRepository.list_for_supplier(profile.id)
    assert len(offers) == 2
    assert all(offer.product_id is not None for offer in offers)


def test_a_second_supplier_lands_on_the_same_catalogue_products(
    make_supplier, make_supplier_profile
):
    """THE WHOLE POINT, and the reason a shared catalogue exists.

    Two suppliers, two completely different spellings, one barcode each.
    Under v1 these were unrelated rows and "who sells this cheaper" had
    no answer. Here they converge on one product and the comparison
    becomes possible."""
    first = make_supplier_profile(make_supplier("a@example.com"), business_name="A Wholesale")
    _run(first.id, "a.csv", WITH_BARCODES)
    assert Product.query.count() == 2

    second = make_supplier_profile(make_supplier("b@example.com"), business_name="B Distributors")
    differently_worded = (
        b"name,category,price,unit,sku,barcode\n"
        b"COKE 2LT PET,Beverages,24.50,Each,COKE-2,5449000054227\n"
    )
    _run(second.id, "b.csv", differently_worded)

    assert Product.query.count() == 2, "the barcode matched; no new product was invented"

    coke = Product.query.filter_by(gtin="5449000054227").one()
    offers = SupplierOfferRepository.list_for_supplier(second.id)
    assert offers[0].product_id == coke.id

    linked = [
        offer
        for supplier in (first, second)
        for offer in SupplierOfferRepository.list_for_supplier(supplier.id)
        if offer.product_id == coke.id
    ]
    assert len(linked) == 2, "two suppliers, one product -- this is what makes comparison possible"
    assert {offer.price_cents for offer in linked} == {2200, 2450}


def test_pack_size_finally_reaches_the_offer_through_an_import(
    make_supplier, make_supplier_profile
):
    """A REAL GAP THIS CLOSES. unit_quantity/unit_measure existed on the
    model and on the single-product form, but no import could set them
    -- so a supplier with 3,000 pack products had to enter pack sizes
    one at a time by hand."""
    profile = make_supplier_profile(make_supplier())
    _run(profile.id, "week1.csv", WITH_BARCODES)

    coke = next(
        offer
        for offer in SupplierOfferRepository.list_for_supplier(profile.id)
        if offer.sku == "CC2L"
    )
    assert coke.unit_quantity == 2
    assert coke.unit_measure.value == "L"


def test_a_barcode_match_is_recorded_as_auto_applied(make_supplier, make_supplier_profile):
    """Every link is explainable. A supplier disputing a match is owed
    which tier proposed it, at what confidence, on what text."""
    first = make_supplier_profile(make_supplier("a@example.com"), business_name="A Wholesale")
    _run(first.id, "a.csv", WITH_BARCODES)

    second = make_supplier_profile(make_supplier("b@example.com"), business_name="B Distributors")
    _run(
        second.id,
        "b.csv",
        b"name,category,price,unit,sku,barcode\nCOKE 2LT,Beverages,24.50,Each,C2,5449000054227\n",
    )

    review = (
        MatchReview.query.filter_by(source_text="COKE 2LT").one()
    )
    assert review.status is ReviewStatus.AUTO_APPLIED
    assert review.tier == "BARCODE"
    assert float(review.confidence) == 1.0
    assert "Barcode" in review.reason


def test_a_file_with_no_new_columns_still_imports_exactly_as_before(
    make_supplier, make_supplier_profile
):
    """BACKWARD COMPATIBILITY, asserted rather than assumed. Every
    supplier who already has a template must keep working -- the four
    matching columns are optional and a file without them is not
    degraded, only unmatched by barcode."""
    profile = make_supplier_profile(make_supplier())
    old_style = (
        b"name,category,price,unit,quantity\n"
        b"Bread White,Bakery,19.99,Each,40\n"
    )

    job = _run(profile.id, "old.csv", old_style)

    assert job.error_rows == 0
    assert job.created_rows == 1
    offers = SupplierOfferRepository.list_for_supplier(profile.id)
    assert offers[0].name == "Bread White"
    assert offers[0].unit_quantity is None


def test_a_malformed_barcode_costs_the_barcode_not_the_row(
    make_supplier, make_supplier_profile
):
    """CHANGED 2026-09-11, deliberately. This test used to assert the
    opposite -- created_rows == 1 for this two-row file, because the row
    with the bad barcode was discarded entirely.

    That contradicted row_validator's own comment ("ALL FOUR ARE
    OPTIONAL AND NONE OF THEM CAN FAIL A ROW") and it is the wrong
    product behaviour: on a 3,000-line file, forty barcode typos meant
    forty products that never existed and no business could buy. The
    bad VALUE is dropped, the row imports, the supplier is told."""
    profile = make_supplier_profile(make_supplier())
    payload = (
        b"name,category,price,unit,barcode\n"
        b"Coca-Cola 2L,Beverages,22.00,Each,not-a-barcode\n"
        b"Bread White,Bakery,19.99,Each,\n"
    )

    job = _run(profile.id, "messy.csv", payload)

    assert job.created_rows == 2, "a bad OPTIONAL value must not discard the product"
    assert job.error_rows == 0, "no row failed"
    assert any(
        "Barcode" in error.message for error in ImportJobRepository.list_errors(job.id)
    ), "but the supplier is still told about it"


def test_a_barcode_with_a_bad_check_digit_is_not_trusted(
    make_supplier, make_supplier_profile
):
    """THE DANGEROUS CASE, and the reason gtin.py exists.

    A one-digit typo in a barcode is usually not a near-miss -- barcodes
    are densely allocated, so it frequently lands on ANOTHER REAL
    PRODUCT, which tier 0 would then link with confidence 1.0 and the
    words "matches this product exactly".

    5449000054227 is Coca-Cola's real EAN-13. 5449000054228 is one digit
    out, fails its check digit, and must never reach the barcode tier."""
    profile = make_supplier_profile(make_supplier())
    payload = (
        b"name,category,price,unit,sku,barcode\n"
        b"Coca-Cola Original 2L,Beverages,22.00,Each,CC1,5449000054227\n"
        b"Something Else 2L,Beverages,21.00,Each,SE1,5449000054228\n"
    )

    job = _run(profile.id, "typo.csv", payload)

    assert job.created_rows == 2, "both products import"
    assert job.error_rows == 0

    # The sound barcode reached the catalogue; the typo did not.
    assert Product.query.filter_by(gtin="5449000054227").count() == 1
    assert Product.query.filter_by(gtin="5449000054228").count() == 0


def test_matching_can_be_switched_off_without_breaking_imports(
    make_supplier, make_supplier_profile, monkeypatch
):
    """The kill switch, proven where it matters. Off means offers import
    normally and stay unmatched -- exactly how they behaved before the
    catalogue existed."""
    monkeypatch.setenv("MATCHING_ENABLED", "false")
    profile = make_supplier_profile(make_supplier())

    job = _run(profile.id, "week1.csv", WITH_BARCODES)

    assert job.created_rows == 2
    assert job.error_rows == 0
    assert Product.query.count() == 0, "no catalogue rows were created"
