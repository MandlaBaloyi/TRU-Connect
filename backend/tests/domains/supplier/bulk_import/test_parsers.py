"""
spreadsheet_parser + row_validator tests -- formalizes the direct
manual verification already run against real CSV/XLSX content.
"""
from __future__ import annotations

import io

import openpyxl
import pytest

from src.domains.supplier.bulk_import.parsers.spreadsheet_parser import (
    UnsafeSpreadsheetError,
    parse_csv_bytes,
    parse_xlsx_bytes,
)
from src.domains.supplier.bulk_import.validators.row_validator import (
    match_category,
    match_unit,
    parse_cents_input,
    parse_quantity,
    validate_row,
)
from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit


class TestRowValidator:
    def test_valid_row_parses_cleanly(self):
        row = validate_row(
            {"name": "Coca-Cola 500ml", "category": "Beverages", "price": "12.00", "unit": "Each", "quantity": "47"},
            row_number=2,
        )
        assert row.is_valid
        assert row.category == ProductCategory.BEVERAGES
        assert row.price_cents == 1200
        assert row.selling_unit == ProductUnit.EACH
        assert row.quantity == 47

    def test_blank_quantity_defaults_to_zero(self):
        row = validate_row({"name": "Bread", "category": "Bakery", "price": "19.99", "unit": "Each"}, row_number=3)
        assert row.is_valid
        assert row.quantity == 0

    def test_price_accepts_r_prefix_and_comma_decimal(self):
        assert parse_cents_input("R12,50") == 1250
        assert parse_cents_input("12.50") == 1250
        assert parse_cents_input("R 12.50") == 1250

    def test_price_rejects_garbage(self):
        assert parse_cents_input("garbage") is None
        assert parse_cents_input("") is None

    def test_category_matches_label_case_insensitively(self):
        assert match_category("beverages") == ProductCategory.BEVERAGES
        assert match_category("Snacks & Confectionery") == ProductCategory.SNACKS_CONFECTIONERY

    def test_category_also_accepts_internal_code(self):
        assert match_category("BEVERAGES") == ProductCategory.BEVERAGES

    def test_category_rejects_unknown_value(self):
        assert match_category("NotARealCategory") is None

    def test_unit_matches_label_and_code(self):
        assert match_unit("each") == ProductUnit.EACH
        assert match_unit("BOTTLE") == ProductUnit.BOTTLE

    def test_multiple_errors_collected_at_once_not_just_first(self):
        row = validate_row({"name": "", "category": "", "price": "garbage", "unit": ""}, row_number=6)
        assert len(row.errors) == 4
        assert {e.field for e in row.errors} == {"name", "category", "price", "unit"}

    def test_quantity_rejects_non_numeric(self):
        value, error = parse_quantity("abc")
        assert value is None
        assert "Invalid quantity" in error

    def test_image_references_track_column_not_just_flat_list(self):
        row = validate_row(
            {"name": "X", "category": "Other", "price": "1.00", "unit": "Each", "image_1": "", "image_2": "b.jpg"},
            row_number=2,
        )
        assert len(row.image_references) == 1
        assert row.image_references[0].column == "image_2"
        assert row.image_references[0].filename == "b.jpg"

    def test_category_typo_gets_a_did_you_mean_suggestion(self):
        """A real typo ("Beveragse") gets a suggestion, never an
        auto-correction -- the row still fails, but points the
        supplier at the fix rather than leaving them guessing."""
        row = validate_row({"name": "X", "category": "Beveragse", "price": "1.00", "unit": "Each"}, row_number=2)

        assert not row.is_valid
        category_error = next(e for e in row.errors if e.field == "category")
        assert "Beveragse" in category_error.message
        assert 'Did you mean "Beverages"?' in category_error.message

    def test_unit_typo_gets_a_did_you_mean_suggestion(self):
        row = validate_row({"name": "X", "category": "Other", "price": "1.00", "unit": "Eahc"}, row_number=2)

        assert not row.is_valid
        unit_error = next(e for e in row.errors if e.field == "unit")
        assert 'Did you mean "Each"?' in unit_error.message

    def test_wildly_wrong_category_gets_no_suggestion_rather_than_a_bad_guess(self):
        """A value with no real resemblance to anything valid should
        get a plain error, not a low-confidence guess dressed up as
        a suggestion."""
        row = validate_row({"name": "X", "category": "zzzzzzzzzz", "price": "1.00", "unit": "Each"}, row_number=2)

        category_error = next(e for e in row.errors if e.field == "category")
        assert "Did you mean" not in category_error.message

    # --- sku / description / compare_at_price -- all genuinely optional ---

    def test_sku_description_compare_at_price_are_all_optional(self):
        row = validate_row(
            {"name": "Bread", "category": "Bakery", "price": "18.50", "unit": "Each"}, row_number=2
        )

        assert row.is_valid
        assert row.sku is None
        assert row.description is None
        assert row.compare_at_price_cents is None

    def test_sku_is_passed_through_when_provided(self):
        row = validate_row(
            {"name": "Bread", "category": "Bakery", "price": "18.50", "unit": "Each", "sku": "BREAD-CASE-24"},
            row_number=2,
        )

        assert row.is_valid
        assert row.sku == "BREAD-CASE-24"

    def test_description_is_passed_through_when_provided(self):
        row = validate_row(
            {
                "name": "Bread",
                "category": "Bakery",
                "price": "18.50",
                "unit": "Each",
                "description": "3 loaves per case.",
            },
            row_number=2,
        )

        assert row.is_valid
        assert row.description == "3 loaves per case."

    def test_compare_at_price_is_parsed_when_valid_and_higher_than_price(self):
        row = validate_row(
            {
                "name": "Bread",
                "category": "Bakery",
                "price": "18.50",
                "unit": "Each",
                "compare_at_price": "25.00",
            },
            row_number=2,
        )

        assert row.is_valid
        assert row.compare_at_price_cents == 2500

    def test_compare_at_price_below_price_is_a_real_row_error(self):
        """Same rule as the single-product form's own validation --
        caught here too so a supplier sees this in the PREVIEW, before
        ever submitting."""
        row = validate_row(
            {
                "name": "Bread",
                "category": "Bakery",
                "price": "18.50",
                "unit": "Each",
                "compare_at_price": "10.00",
            },
            row_number=2,
        )

        assert not row.is_valid
        error = next(e for e in row.errors if e.field == "compare_at_price")
        assert "higher than the actual price" in error.message

    def test_invalid_compare_at_price_text_is_a_real_row_error(self):
        row = validate_row(
            {
                "name": "Bread",
                "category": "Bakery",
                "price": "18.50",
                "unit": "Each",
                "compare_at_price": "not a number",
            },
            row_number=2,
        )

        assert not row.is_valid
        error = next(e for e in row.errors if e.field == "compare_at_price")
        assert "Invalid compare-at price" in error.message


class TestParseCsv:
    def test_parses_real_csv_correctly(self):
        csv_bytes = (
            b"name,category,price,unit,quantity,image_1\n"
            b"Coca-Cola 500ml,Beverages,12.00,Each,47,coke500.jpg\n"
            b"Bread,Bakery,19.99,Each,,\n"
        )
        parsed = parse_csv_bytes(csv_bytes)

        assert len(parsed.rows) == 2
        assert all(r.is_valid for r in parsed.rows)
        assert parsed.rows[0].quantity == 47
        assert parsed.rows[1].quantity == 0

    def test_detects_missing_required_columns(self):
        parsed = parse_csv_bytes(b"name,price\nBread,10.00\n")
        assert set(parsed.missing_required_columns) == {"category", "unit"}

    def test_detects_unrecognized_columns(self):
        parsed = parse_csv_bytes(b"name,category,price,unit,notacolumn\nX,Other,1.00,Each,y\n")
        assert "notacolumn" in parsed.unrecognized_columns

    def test_rejects_too_many_rows(self):
        lines = ["name,category,price,unit"] + [f"p{i},Other,1.00,Each" for i in range(10_001)]
        csv_bytes = ("\n".join(lines)).encode("utf-8")
        with pytest.raises(UnsafeSpreadsheetError, match="too many rows"):
            parse_csv_bytes(csv_bytes)

    def test_rejects_oversized_file(self):
        big = b"name,category,price,unit\n" + b"a" * (21 * 1024 * 1024)
        with pytest.raises(UnsafeSpreadsheetError, match="too large"):
            parse_csv_bytes(big)


class TestParseXlsx:
    def _make_xlsx_bytes(self, rows) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        for row in rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def test_parses_real_xlsx_correctly(self):
        raw = self._make_xlsx_bytes(
            [
                ["name", "category", "price", "unit", "quantity"],
                ["Simba Chips", "Snacks & Confectionery", "18.50", "Each", "24"],
            ]
        )
        parsed = parse_xlsx_bytes(raw)

        assert len(parsed.rows) == 1
        assert parsed.rows[0].is_valid
        assert parsed.rows[0].quantity == 24

    def test_skips_genuinely_blank_rows(self):
        raw = self._make_xlsx_bytes(
            [
                ["name", "category", "price", "unit"],
                ["X", "Other", "1.00", "Each"],
                [None, None, None, None],
            ]
        )
        parsed = parse_xlsx_bytes(raw)
        assert len(parsed.rows) == 1
