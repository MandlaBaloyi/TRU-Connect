"""
Regenerate the supplier import template (XLSX) from the canonical field
list.

WHY THIS IS A SCRIPT AND NOT A HAND-EDITED FILE. The template used to be
a spreadsheet somebody made once and saved into the app's assets. V2 step
6e added four columns to the importer -- barcode, brand, pack_quantity,
pack_unit -- and the template was never touched, so for weeks a supplier
who downloaded our OFFICIAL template and filled it in perfectly got zero
barcode matches. The single most valuable column in the file was
invisible to everyone who followed our own instructions.

Generating it from IMPORT_FIELDS makes that class of drift impossible:
add a column to fields.py, run this, and the template, the parser, the
validator and the help text all agree because they come from one place.

    python scripts/generate_import_template.py

Writes to frontend/mobile/assets/bulk-import/, which is where the app
bundles it from. Commit the result -- it is a build artefact we ship, not
something generated at runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

from src.domains.catalogue.products.models.taxonomy import (  # noqa: E402
    ProductCategory,
    ProductUnit,
)
from src.domains.supplier.bulk_import.fields import IMPORT_FIELDS  # noqa: E402
from src.domains.supplier.bulk_import.validators.row_validator import (  # noqa: E402
    _CATEGORY_LABELS,
    _UNIT_LABELS,
)

OUTPUT = (
    BACKEND.parent
    / "frontend"
    / "mobile"
    / "assets"
    / "bulk-import"
    / "TRU_Connect_Product_Import_Template.xlsx"
)

HEADER_FILL = PatternFill("solid", fgColor="0B2545")
REQUIRED_FILL = PatternFill("solid", fgColor="1D4E89")
HEADER_FONT = Font(bold=True, color="FFFFFF")

#: Example rows, written against the live field list rather than typed
#: out, so a new column cannot leave the examples short. Values are
#: keyed by field name; anything missing is simply blank, which is
#: itself a useful demonstration that most columns are optional.
EXAMPLES = [
    {
        "name": "Coca-Cola Original 2L",
        "category": "Beverages",
        "price": "22.00",
        "unit": "Each",
        "quantity": "47",
        "sku": "CC-2L",
        "description": "2L PET bottle.",
        "barcode": "5449000054227",
        "brand": "Coca-Cola",
        "pack_quantity": "2",
        "pack_unit": "L",
        "image_1": "coke2l.jpg",
    },
    {
        "name": "Iwisa Super Maize Meal 10kg",
        "category": "Food & Grocery",
        "price": "119.99",
        "unit": "Bag",
        "quantity": "24",
        "sku": "IW-10",
        "brand": "Iwisa",
        "pack_quantity": "10",
        "pack_unit": "kg",
    },
    {
        "name": "Albany White Bread 700g",
        "category": "Bakery",
        "price": "19.99",
        "unit": "Each",
        "quantity": "0",
        "description": "Sliced white, 1 loaf per unit.",
    },
]


def _autosize(ws, max_width: int = 60) -> None:
    for column in ws.columns:
        longest = max((len(str(c.value)) for c in column if c.value is not None), default=0)
        letter = get_column_letter(column[0].column)
        ws.column_dimensions[letter].width = min(max(12, longest + 2), max_width)


def build() -> Workbook:
    wb = Workbook()

    # --- Products -------------------------------------------------------
    ws = wb.active
    ws.title = "Products"
    names = [f.name for f in IMPORT_FIELDS]
    ws.append(names)
    for index, field in enumerate(IMPORT_FIELDS, start=1):
        cell = ws.cell(row=1, column=index)
        cell.font = HEADER_FONT
        # Required columns are a different colour, so "which of these do
        # I actually have to fill in" is answerable at a glance rather
        # than by reading the Instructions sheet.
        cell.fill = HEADER_FILL if field.required else REQUIRED_FILL
        cell.alignment = Alignment(horizontal="center")
    for example in EXAMPLES:
        ws.append([example.get(name) for name in names])
    ws.freeze_panes = "A2"
    _autosize(ws)

    # --- Instructions ---------------------------------------------------
    ws = wb.create_sheet("Instructions")
    ws.append(["How to fill in this template"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])
    ws.append(["Column", "Required?", "What it is"])
    for cell in ws[3]:
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
    for field in IMPORT_FIELDS:
        ws.append([field.name, "Required" if field.required else "Optional", field.help_text])
    ws.append([])
    ws.append([
        "Tip",
        "",
        "The barcode column is the most useful one you can fill in. A barcode matches your "
        "product to the TRU Connect catalogue exactly, so businesses can compare it against "
        "other suppliers. Everything else is matched on the words you type.",
    ])
    for row in ws.iter_rows(min_row=4):
        row[2].alignment = Alignment(wrap_text=True, vertical="top")
    _autosize(ws, max_width=90)

    # --- Categories -----------------------------------------------------
    ws = wb.create_sheet("Categories")
    ws.append(["Valid category names"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append(["Type one of these exactly into the category column."])
    ws.append([])
    for category in ProductCategory:
        ws.append([_CATEGORY_LABELS.get(category, category.value)])
    _autosize(ws)

    # --- Units ----------------------------------------------------------
    ws = wb.create_sheet("Units")
    ws.append(["Valid unit names"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append(['Type one of these exactly into the unit column ("Sold as").'])
    ws.append([])
    for unit in ProductUnit:
        ws.append([_UNIT_LABELS.get(unit, unit.value)])
    _autosize(ws)

    return wb


if __name__ == "__main__":
    workbook = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(OUTPUT)
    print(f"wrote {OUTPUT}")
    print(f"  {len(IMPORT_FIELDS)} columns: {', '.join(f.name for f in IMPORT_FIELDS)}")
