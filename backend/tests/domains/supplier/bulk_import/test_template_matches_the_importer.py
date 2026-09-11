"""
The downloadable template must agree with the importer that reads it.

THE BUG THIS PREVENTS ALREADY HAPPENED. V2 step 6e added barcode, brand,
pack_quantity and pack_unit to the importer. The template shipped in the
app's assets was never regenerated, so for weeks a supplier who
downloaded our OFFICIAL template and filled it in perfectly produced
zero barcode matches -- the single most valuable column in the file was
invisible to everyone who followed our own instructions.

Nothing failed. No test broke. The importer was correct, the template
was correct when it was made, and the two had simply drifted apart. That
is exactly the kind of defect a test has to catch, because a human
reading either file alone sees nothing wrong.

Regenerate with:  python scripts/generate_import_template.py
"""
from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest

from src.domains.supplier.bulk_import.fields import IMPORT_FIELDS
from src.domains.supplier.bulk_import.parsers.spreadsheet_parser import (
    REQUIRED_COLUMNS,
    parse_xlsx_bytes,
)

TEMPLATE = (
    Path(__file__).resolve().parents[4].parent
    / "frontend"
    / "mobile"
    / "assets"
    / "bulk-import"
    / "TRU_Connect_Product_Import_Template.xlsx"
)


@pytest.fixture(scope="module")
def headers() -> list:
    assert TEMPLATE.exists(), f"template missing at {TEMPLATE}"
    workbook = openpyxl.load_workbook(TEMPLATE)
    return [cell.value for cell in workbook["Products"][1]]


def test_the_template_offers_every_column_the_importer_understands(headers):
    """A column the importer reads but the template omits is a feature
    nobody can reach."""
    missing = [field.name for field in IMPORT_FIELDS if field.name not in headers]
    assert not missing, (
        f"the importer understands {missing} but the template does not offer them -- "
        "run scripts/generate_import_template.py"
    )


def test_the_template_offers_nothing_the_importer_ignores(headers):
    """And the reverse: a column in the template that the importer does
    not read is a promise we silently break."""
    known = {field.name for field in IMPORT_FIELDS}
    unknown = [h for h in headers if h and h not in known]
    assert not unknown, f"the template offers {unknown}, which the importer ignores"


def test_the_template_carries_every_required_column(headers):
    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    assert not missing, f"required columns absent from the template: {missing}"


def test_the_template_actually_parses_and_its_examples_are_valid():
    """The strongest version of this test: feed the shipped template
    THROUGH THE REAL PARSER. Headers agreeing is necessary; example rows
    that survive validation is proof."""
    parsed = parse_xlsx_bytes(TEMPLATE.read_bytes())

    assert not parsed.missing_required_columns
    assert not parsed.unrecognized_columns
    assert parsed.rows, "the template should ship with example rows"
    for row in parsed.rows:
        assert not row.errors, f"example row {row.row_number} does not validate: {row.errors}"


def test_the_example_row_demonstrates_a_real_barcode():
    """The example barcode has to be arithmetically sound, or we are
    teaching suppliers to send us numbers our own check digit rejects."""
    from src.domains.catalogue.matching.algorithms import gtin

    parsed = parse_xlsx_bytes(TEMPLATE.read_bytes())
    barcodes = [row.barcode for row in parsed.rows if row.barcode]
    assert barcodes, "at least one example should show a barcode"
    for code in barcodes:
        assert gtin.is_catalogue_usable(code), f"example barcode {code} is not usable"
