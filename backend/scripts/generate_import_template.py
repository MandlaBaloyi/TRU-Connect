"""
Regenerate the supplier import template (XLSX) AND the import guide
(DOCX) from the canonical field list.

WHY THIS IS A SCRIPT AND NOT A HAND-EDITED FILE. The template used to be
a spreadsheet somebody made once and saved into the app's assets. V2 step
6e added four columns to the importer -- barcode, brand, pack_quantity,
pack_unit -- and the template was never touched, so for weeks a supplier
who downloaded our OFFICIAL template and filled it in perfectly got zero
barcode matches. The single most valuable column in the file was
invisible to everyone who followed our own instructions.

The GUIDE had drifted the same way and for the same reason -- its
column-reference table still described the eight original columns.
A supplier reading our own documentation had no way to learn that a
barcode column existed.

Generating both from IMPORT_FIELDS makes that class of drift
impossible: add a column to fields.py, run this, and the template, the
guide, the parser, the validator and the help text all agree because
they come from one place.

    python scripts/generate_import_template.py

Writes both files to frontend/mobile/assets/bulk-import/, which is where
the app bundles them from. Commit the results -- they are build artefacts
we ship, not something generated at runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from docx import Document  # noqa: E402
from docx.shared import Pt  # noqa: E402
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

ASSETS = BACKEND.parent / "frontend" / "mobile" / "assets" / "bulk-import"
OUTPUT = ASSETS / "TRU_Connect_Product_Import_Template.xlsx"
GUIDE_OUTPUT = ASSETS / "TRU_Connect_Bulk_Import_Guide.docx"

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
        "product to the TruConnect catalogue exactly, so businesses can compare it against "
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



def _table(document, headers, rows):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Light Grid Accent 1"
    for cell, text in zip(table.rows[0].cells, headers):
        cell.text = text
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    for row in rows:
        cells = table.add_row().cells
        for cell, text in zip(cells, row):
            cell.text = str(text)
    return table


def build_guide() -> Document:
    """The supplier-facing guide.

    THE PROSE IS WRITTEN HERE; THE TABLES ARE GENERATED. That split is
    the whole point -- the wording is a human judgement worth keeping,
    and the column list is a fact that must never disagree with the
    importer. The previous guide was entirely hand-written, so when four
    columns were added its reference table silently became wrong and a
    supplier reading our own documentation could not learn that a
    barcode column existed.
    """
    doc = Document()
    doc.add_heading("TruConnect", level=0)
    doc.add_heading("Bulk Product Import Guide", level=1)
    doc.add_paragraph(
        "How to publish your whole product catalogue at once, using a "
        "spreadsheet and a ZIP of photos."
    )

    doc.add_heading("Who this is for", level=2)
    doc.add_paragraph(
        "If you already keep your stock list in a spreadsheet -- Excel, Google "
        "Sheets exported as CSV, or a price file your own system produces -- you "
        "do not need to retype it. Upload it, check the preview, and your whole "
        "range goes live at once."
    )

    doc.add_heading("Overview", level=2)
    for index, step in enumerate(
        [
            ("Download the template", 'Get "TruConnect Product Import Template.xlsx" from the Bulk Products screen.'),
            ("Fill it in", "One row per product. Delete the example rows first -- they are there to show the shape."),
            ("Prepare your photos", "Put every image in one ZIP file. Filenames must exactly match what you typed."),
            ("Upload both files", "Your spreadsheet and your images ZIP, from the Import Products screen."),
            ("Review before you confirm", "TruConnect shows you every row -- which are ready, and exactly what is wrong with the rest."),
            ("Fix and re-upload if needed", "Rows with problems do not stop the others. Include your SKU column and a re-upload UPDATES your products instead of duplicating them."),
        ],
        start=1,
    ):
        paragraph = doc.add_paragraph(style="List Number")
        run = paragraph.add_run(step[0] + " -- ")
        run.bold = True
        paragraph.add_run(step[1])

    doc.add_heading("The one column worth filling in", level=2)
    doc.add_paragraph(
        "If you fill in nothing else optional, fill in barcode. A barcode "
        "identifies your product exactly, which means it is matched to the TRU "
        "Connect catalogue instantly and correctly -- so a business can compare "
        "your price against other suppliers for the same item, and find you. "
        "Everything else is matched on the words you typed, which works, but not "
        "as well."
    )
    doc.add_paragraph(
        "Use the barcode printed on the item itself. In-store labels your own "
        "shop prints (they usually begin 02, 04 or 2) are not global barcodes and "
        "cannot be used -- the row still imports, just without one."
    )

    doc.add_heading("Column reference", level=2)
    doc.add_paragraph(
        "These are the exact column headers the template uses. Column order does "
        "not matter, but the header text must match."
    )
    _table(
        doc,
        ["Column", "Required?", "What to put there"],
        [
            (field.name, "Required" if field.required else "Optional", field.help_text)
            for field in IMPORT_FIELDS
        ],
    )

    doc.add_heading("Categories", level=2)
    doc.add_paragraph("The category column must exactly match one of these:")
    labels = [_CATEGORY_LABELS.get(c, c.value) for c in ProductCategory]
    _table(doc, ["Category", "Category"],
           [(labels[i], labels[i + 1] if i + 1 < len(labels) else "")
            for i in range(0, len(labels), 2)])

    doc.add_heading('Units ("Sold as")', level=2)
    doc.add_paragraph("The unit column must exactly match one of these:")
    units = [_UNIT_LABELS.get(u, u.value) for u in ProductUnit]
    _table(doc, ["Unit", "Unit"],
           [(units[i], units[i + 1] if i + 1 < len(units) else "")
            for i in range(0, len(units), 2)])

    doc.add_heading("Images", level=2)
    doc.add_paragraph(
        "Put every photo in a single ZIP file. Folders inside the ZIP are fine -- "
        "TruConnect looks at filenames, not paths. Accepted formats: .jpg, "
        ".jpeg, .png, .webp."
    )
    doc.add_paragraph(
        "A filename in image_1 to image_5 must exactly match a file inside the "
        "ZIP, including the extension."
    )
    doc.add_paragraph(
        "Images are entirely optional. A product with none still imports and "
        "publishes -- TruConnect shows a category picture in the meantime, so "
        "your shopfront does not look empty while you photograph your range."
    )

    doc.add_heading("If something does not work", level=2)
    _table(
        doc,
        ["If you see...", "What it means"],
        [
            ("Category not recognised", "The category text does not match the Categories list exactly."),
            ("Unit not recognised", "Same, for the unit column."),
            ("Invalid price", "The price cell is not a plain number. Remove currency symbols and spaces."),
            ("Barcode failed its check digit", "One digit is probably wrong. The row imports without it."),
            ("In-store barcode", "That code is only unique inside one shop, so it cannot identify the product."),
            ("Image not found in ZIP", "The filename does not match a file in the ZIP. Check the extension."),
            ("SKU appears more than once", "Two rows share a SKU. Each product needs its own."),
        ],
    )

    doc.add_paragraph()
    footer = doc.add_paragraph()
    note = footer.add_run(
        "This guide is generated from the importer itself, so the column "
        "reference above is always what the system actually reads."
    )
    note.italic = True
    note.font.size = Pt(9)
    return doc


def _save(document, path: Path) -> bool:
    """Write one artefact, and say plainly if it could not be written.

    ON WINDOWS AN OPEN FILE CANNOT BE REPLACED, and both of these are
    documents somebody may well have open to look at. Crashing halfway
    would leave one regenerated and the other stale -- which is exactly
    the drift this script exists to prevent -- so each is attempted
    independently and the failure names the fix.
    """
    try:
        document.save(path)
    except PermissionError:
        print(f"  SKIPPED {path.name}: the file is open. Close it and run this again.")
        return False
    print(f"  wrote {path.name}")
    return True


if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)

    ok = _save(build(), OUTPUT)
    ok = _save(build_guide(), GUIDE_OUTPUT) and ok

    print(f"  {len(IMPORT_FIELDS)} columns: {', '.join(f.name for f in IMPORT_FIELDS)}")
    sys.exit(0 if ok else 1)
