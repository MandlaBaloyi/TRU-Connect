/**
 * importColumns.ts — THE single source of truth for the Import
 * Products spreadsheet contract. Every other piece of this feature
 * reads from here rather than hardcoding column names a second time:
 * parseSpreadsheet.ts (maps file headers to fields), the validator
 * (knows what's required), generate_import_template.py (the
 * downloadable XLSX -- built once from this exact list, not typed out
 * separately), and the Word guide (describes these same columns). If
 * a column ever needs to change, it changes here once.
 *
 * v2: 3 image columns -> 5 (per review, suppliers wanted more than
 * three photos per row). "stock" (a text In/Out toggle) is GONE,
 * replaced by "quantity" -- a plain number that seeds the new
 * product's real Inventory record (quantityOnHand) the moment it's
 * created. This wasn't just an add -- keeping the old text "stock"
 * column alongside a new numeric "quantity" column would let a file
 * say "Out of stock" with quantity=50 in the same row, an outright
 * contradiction. Once Inventory computes status FROM quantity (see
 * this whole app's Products/Inventory migration), quantity is the
 * only honest source of truth an import file can provide.
 *
 * Category/unit values in the FILE are human-readable LABELS
 * ("Beverages", "Bottle"), never TRU Connect's internal codes
 * ("BEVERAGES", "BOTTLE") -- a supplier filling in a spreadsheet
 * should never need to know our enum codes. The parser matches
 * case-insensitively against CATEGORY_OPTIONS/UNIT_OPTIONS' own labels
 * (also accepting the raw code, so a supplier re-uploading TRU
 * Connect's own export still works) and flags "Category not
 * recognised" on a genuine miss -- never a fuzzy guess.
 */

export interface ImportColumnSpec {
  /** Exact header text expected in row 1, case-insensitive match. */
  header: string;
  required: boolean;
  description: string;
}

export const IMPORT_COLUMNS: readonly ImportColumnSpec[] = [
  { header: "name", required: true, description: "Product name, e.g. \"Coca-Cola 500ml\"." },
  {
    header: "category",
    required: true,
    description: "Must match one of TRU Connect's category names exactly (see the Categories sheet).",
  },
  { header: "price", required: true, description: "Rands, e.g. 12.00 or 12,00. No currency symbol needed." },
  {
    header: "unit",
    required: true,
    description: "What the price is for, e.g. \"Each\" or \"Case\" (see the Units sheet).",
  },
  {
    header: "quantity",
    required: false,
    description: "How many you currently have. Leave blank to start at 0 (Out of stock until you add stock).",
  },
  {
    header: "sku",
    required: false,
    description: "Your own tracking label. Leave blank and we'll generate one for you automatically.",
  },
  {
    header: "description",
    required: false,
    description: "Plain text, e.g. \"3 loaves per case.\" Shown to businesses when they order.",
  },
  {
    header: "compare_at_price",
    required: false,
    description: "The \"was\" price for a sale, e.g. 25.00. Must be higher than price. Leave blank if not running one.",
  },
  {
    header: "image_1",
    required: false,
    description: "Filename of the main photo, exactly as it appears inside your images ZIP, e.g. \"coke500.jpg\".",
  },
  { header: "image_2", required: false, description: "A second photo filename, optional." },
  { header: "image_3", required: false, description: "A third photo filename, optional." },
  { header: "image_4", required: false, description: "A fourth photo filename, optional." },
  { header: "image_5", required: false, description: "A fifth photo filename, optional." },
] as const;

export const REQUIRED_COLUMN_HEADERS: readonly string[] = IMPORT_COLUMNS.filter((c) => c.required).map(
  (c) => c.header
);

export const KNOWN_COLUMN_HEADERS: readonly string[] = IMPORT_COLUMNS.map((c) => c.header);

export const IMAGE_COLUMN_HEADERS: readonly string[] = ["image_1", "image_2", "image_3", "image_4", "image_5"];
