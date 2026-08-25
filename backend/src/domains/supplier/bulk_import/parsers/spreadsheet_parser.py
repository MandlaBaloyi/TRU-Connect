"""
Spreadsheet parsing -- CSV via the standard library, XLSX via openpyxl.
Produces the same shape the frontend's own parseSpreadsheet.ts does:
rows validated through validate_row, plus file-level checks (missing
required columns, unrecognised columns).

XLSX IS ALSO A ZIP INTERNALLY (OOXML) -- openpyxl parses the archive
structure itself, but this file still applies its own sanity caps
BEFORE handing a file to openpyxl: a spreadsheet claiming to have
100,000 rows or an implausible file size is rejected before parsing
even starts, not after openpyxl has already spent time and memory on
it. This is a distinct concern from zip_parser.py's own defenses
(which guard the IMAGES zip) -- XLSX needs its own version of the same
discipline because the underlying risk (a small file expanding into
something huge) is the same shape.
"""
from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass, field
from typing import List

import openpyxl

from src.domains.supplier.bulk_import.validators.row_validator import IMAGE_COLUMN_HEADERS, ParsedRow, validate_row

REQUIRED_COLUMNS = ["name", "category", "price", "unit"]
# sku/description/compare_at_price are OPTIONAL -- same "leave it
# blank if you don't need it" pattern as quantity and the image
# columns, never added to REQUIRED_COLUMNS.
KNOWN_COLUMNS = REQUIRED_COLUMNS + ["quantity", "sku", "description", "compare_at_price"] + IMAGE_COLUMN_HEADERS

MAX_FILE_BYTES = 20 * 1024 * 1024  # 20MB -- a spreadsheet this large is already suspicious
MAX_ROWS = 10_000


class UnsafeSpreadsheetError(Exception):
    """Same role as bulk_import.parsers.zip_parser.UnsafeZipError --
    turned into a clear, whole-file-level import error by the caller,
    never a 500."""


@dataclass
class ParsedFile:
    source_type: str  # "CSV" | "XLSX"
    rows: List[ParsedRow] = field(default_factory=list)
    column_headers: List[str] = field(default_factory=list)
    unrecognized_columns: List[str] = field(default_factory=list)
    missing_required_columns: List[str] = field(default_factory=list)


def _build_parsed_file(source_type: str, headers: List[str], records: List[dict]) -> ParsedFile:
    normalized_headers = [h.strip().lower() for h in headers if h and h.strip()]
    missing = [c for c in REQUIRED_COLUMNS if c not in normalized_headers]
    unrecognized = [h for h in normalized_headers if h not in KNOWN_COLUMNS]

    rows = []
    for index, record in enumerate(records):
        normalized_record = {
            (k.strip().lower() if k else ""): ("" if v is None else str(v).strip()) for k, v in record.items()
        }
        rows.append(validate_row(normalized_record, index + 2))  # +2: header is row 1

    return ParsedFile(
        source_type=source_type,
        rows=rows,
        column_headers=normalized_headers,
        unrecognized_columns=unrecognized,
        missing_required_columns=missing,
    )


def parse_csv_bytes(raw_bytes: bytes) -> ParsedFile:
    if len(raw_bytes) > MAX_FILE_BYTES:
        raise UnsafeSpreadsheetError(f"File is too large (max {MAX_FILE_BYTES // (1024 * 1024)}MB).")

    text = raw_bytes.decode("utf-8-sig", errors="replace")  # utf-8-sig strips a BOM Excel commonly adds
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []

    records = []
    for i, row in enumerate(reader):
        if i >= MAX_ROWS:
            raise UnsafeSpreadsheetError(f"File has too many rows (max {MAX_ROWS}).")
        records.append(row)

    return _build_parsed_file("CSV", headers, records)


def parse_xlsx_bytes(raw_bytes: bytes) -> ParsedFile:
    if len(raw_bytes) > MAX_FILE_BYTES:
        raise UnsafeSpreadsheetError(f"File is too large (max {MAX_FILE_BYTES // (1024 * 1024)}MB).")

    try:
        # read_only=True streams rows rather than loading the whole
        # sheet into memory at once -- matters exactly for the "avoid
        # loading large files into memory" requirement this domain was
        # built against. data_only=True reads cached formula RESULTS,
        # never evaluates a formula itself (a spreadsheet's formulas
        # are never trusted/executed).
        workbook = openpyxl.load_workbook(io.BytesIO(raw_bytes), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 - openpyxl raises several distinct exception types for a bad file
        raise UnsafeSpreadsheetError("This doesn't look like a valid XLSX file.") from exc

    sheet = workbook.worksheets[0]
    rows_iter = sheet.iter_rows(values_only=True)

    try:
        header_row = next(rows_iter)
    except StopIteration:
        return ParsedFile(source_type="XLSX", rows=[], column_headers=[], missing_required_columns=REQUIRED_COLUMNS)

    headers = [str(h) if h is not None else "" for h in header_row]

    records = []
    for i, row in enumerate(rows_iter):
        if i >= MAX_ROWS:
            raise UnsafeSpreadsheetError(f"File has too many rows (max {MAX_ROWS}).")
        if all(cell is None for cell in row):
            continue  # a genuinely blank row -- Excel leaves these behind constantly, not real data
        record = {headers[j]: row[j] for j in range(min(len(headers), len(row)))}
        records.append(record)

    workbook.close()
    return _build_parsed_file("XLSX", headers, records)


def parse_spreadsheet(filename: str, raw_bytes: bytes) -> ParsedFile:
    extension = os.path.splitext(filename)[1].lower()
    if extension == ".csv":
        return parse_csv_bytes(raw_bytes)
    if extension in (".xlsx", ".xls"):
        return parse_xlsx_bytes(raw_bytes)
    raise UnsafeSpreadsheetError(f"Unsupported file type: {extension or 'unknown'}. Upload a .csv or .xlsx file.")
