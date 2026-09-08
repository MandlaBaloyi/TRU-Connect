"""
Re-importing a price file, which is what a real supplier actually does.

THESE TESTS EXIST BECAUSE THE OLD BEHAVIOUR WAS MEASURED, NOT GUESSED.
Before the upsert, running the SAME file twice was verified to break in
two different ways depending on whether it carried SKUs:

  with SKUs   -- the second import created 0 offers and produced one
                 error per row ("SKU is already used by another
                 product"), so a supplier's correct weekly price file
                 was rejected wholesale and blamed on them
  without SKUs -- silent duplicates: "Coca-Cola 2L" twice, SKU-000001
                 and SKU-000002

The one-time import is the exception; the recurring update is the
relationship. Every test below is that second import.
"""
from __future__ import annotations

from src.domains.supplier.bulk_import.models.import_job import ImportRowOutcome
from src.domains.supplier.bulk_import.repositories.import_job_repository import ImportJobRepository
from src.domains.supplier.bulk_import.workers.import_worker import run_import
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository

WEEK_ONE = (
    b"name,category,price,unit,sku\n"
    b"Coca-Cola 2L,Beverages,22.00,Each,COKE-2L\n"
    b"Bread White,Bakery,19.99,Each,BRD-W\n"
)

# Same SKUs, new prices, and one line the supplier has added since.
WEEK_TWO = (
    b"name,category,price,unit,sku\n"
    b"Coca-Cola 2L,Beverages,24.50,Each,COKE-2L\n"
    b"Bread White,Bakery,21.00,Each,BRD-W\n"
    b"Milk 1L,Dairy & Chilled,18.00,Each,MLK-1L\n"
)


def _run(profile_id, filename, payload):
    job = ImportJobRepository.create(profile_id, filename, False)
    run_import(job.id, profile_id, filename, payload, None, None)
    return job


def test_a_second_price_file_updates_instead_of_colliding(
    make_supplier, make_supplier_profile
):
    """The bug this whole step exists for.

    Verified before the fix: the second run created nothing and raised
    'SKU is already used by another product' on every row."""
    profile = make_supplier_profile(make_supplier())
    _run(profile.id, "week1.csv", WEEK_ONE)
    job2 = _run(profile.id, "week2.csv", WEEK_TWO)

    offers = SupplierOfferRepository.list_for_supplier(profile.id)
    assert len(offers) == 3, "two updates and one addition, not five rows"

    by_sku = {o.sku: o for o in offers}
    assert by_sku["COKE-2L"].price_cents == 2450, "the new price must win"
    assert by_sku["BRD-W"].price_cents == 2100
    assert by_sku["MLK-1L"].price_cents == 1800

    assert job2.created_rows == 1
    assert job2.updated_rows == 2
    assert job2.error_rows == 0


def test_the_updated_offer_is_the_same_row_not_a_replacement(
    make_supplier, make_supplier_profile
):
    """Identity has to survive.

    Orders, inventory, storefront sections and pinned products all hang
    off the offer's id. Replacing the row instead of updating it would
    silently detach every one of them."""
    profile = make_supplier_profile(make_supplier())
    _run(profile.id, "week1.csv", WEEK_ONE)
    original_id = SupplierOfferRepository.get_by_sku_for_supplier(profile.id, "COKE-2L").id

    _run(profile.id, "week2.csv", WEEK_TWO)

    assert SupplierOfferRepository.get_by_sku_for_supplier(profile.id, "COKE-2L").id == original_id


def test_rows_without_a_sku_still_create_because_nothing_identifies_them(
    make_supplier, make_supplier_profile
):
    """The honest limit, asserted so nobody 'fixes' it by guessing.

    A blank-SKU row carries nothing that says WHICH existing offer it
    means. Matching on name would be a guess, and a wrong guess
    overwrites a real price. So it creates -- and the supplier controls
    that by including their SKU column."""
    no_sku = b"name,category,price,unit\nCoca-Cola 2L,Beverages,22.00,Each\n"
    profile = make_supplier_profile(make_supplier())
    _run(profile.id, "a.csv", no_sku)
    _run(profile.id, "b.csv", no_sku)

    offers = SupplierOfferRepository.list_for_supplier(profile.id)
    assert len(offers) == 2, "no stable identity means this genuinely cannot be an update"
    assert {o.sku for o in offers} == {"SKU-000001", "SKU-000002"}


def test_every_row_gets_an_outcome_record(make_supplier, make_supplier_profile):
    """The report has to be able to say WHICH lines changed, not just
    how many."""
    profile = make_supplier_profile(make_supplier())
    _run(profile.id, "week1.csv", WEEK_ONE)
    job2 = _run(profile.id, "week2.csv", WEEK_TWO)

    rows = ImportJobRepository.list_rows(job2.id)
    # 2, 3, 4 -- not 1, 2, 3. Row 1 is the header, exactly as the
    # supplier sees it in their spreadsheet, which is the entire point
    # of recording the number they would recognise rather than an index.
    assert [r.row_number for r in rows] == [2, 3, 4]

    by_sku = {r.supplier_sku: r for r in rows}
    assert by_sku["COKE-2L"].outcome == ImportRowOutcome.UPDATED
    assert by_sku["BRD-W"].outcome == ImportRowOutcome.UPDATED
    assert by_sku["MLK-1L"].outcome == ImportRowOutcome.CREATED
    assert all(r.supplier_offer_id is not None for r in rows)

    assert ImportJobRepository.count_rows_by_outcome(job2.id) == {"UPDATED": 2, "CREATED": 1}


def test_a_first_import_is_all_creations(make_supplier, make_supplier_profile):
    """The counters have to distinguish the two cases -- a weekly file
    that reads as all-creations is how a supplier spots that their SKU
    column did not map."""
    profile = make_supplier_profile(make_supplier())
    job = _run(profile.id, "week1.csv", WEEK_ONE)

    assert job.created_rows == 2
    assert job.updated_rows == 0


def test_error_rows_counts_failures_found_while_saving_too(
    make_supplier, make_supplier_profile
):
    """Previously error_rows was frozen at the parse-time figure, so a
    job could report 0 errors while its own report listed two. A number
    that disagrees with the screen next to it makes every other number
    suspect."""
    profile = make_supplier_profile(make_supplier())
    too_long = "X" * 300
    payload = (
        "name,category,price,unit,sku,description\n"
        f"Coca-Cola 2L,Beverages,22.00,Each,COKE-2L,{too_long}\n"
        "Bread White,Bakery,19.99,Each,BRD-W,fine\n"
    ).encode()

    job = _run(profile.id, "week1.csv", payload)

    reported = job.error_rows
    listed = len({e.row_number for e in ImportJobRepository.list_errors(job.id)})
    assert reported == listed, f"job says {reported} error rows, report lists {listed}"


def test_a_repeat_sku_within_one_file_is_an_error_not_an_update(
    make_supplier, make_supplier_profile
):
    """The distinction that makes the upsert safe.

    "This SKU exists from last week" means UPDATE. "This SKU appears
    twice in the file I just sent" means the supplier made a mistake --
    and quietly letting the second row win would delete a line from
    their catalogue without telling them, which is worse than the
    collision error they used to get.
    """
    profile = make_supplier_profile(make_supplier())
    same_sku_twice = (
        b"name,category,price,unit,sku\n"
        b"Bread,Bakery,18.50,Each,SAME-SKU\n"
        b"Milk,Dairy & Chilled,22.00,Each,SAME-SKU\n"
    )

    job = _run(profile.id, "messy.csv", same_sku_twice)

    offers = SupplierOfferRepository.list_for_supplier(profile.id)
    assert len(offers) == 1, "the first row wins; the second is refused, not applied"
    assert offers[0].name == "Bread", "the second row must not overwrite the first"

    assert job.created_rows == 1
    assert job.updated_rows == 0, "a repeat inside one file is never an update"
    assert job.error_rows == 1

    assert any("SAME-SKU" in e.message for e in ImportJobRepository.list_errors(job.id))
