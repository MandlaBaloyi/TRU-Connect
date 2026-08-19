/**
 * Bulk Products — a genuinely separate supplier tool from Products
 * (per direct review: "don't mix bulk products with individual" --
 * Products stays a simple 1-50-item, one-at-a-time screen; Bulk
 * Products is its own set of routes for different jobs entirely, no
 * longer with its own Account tile -- both destinations below are now
 * reached directly from Products' own shortcuts/header menu instead).
 * Two distinct capabilities live here:
 *
 * 1. BULK EDIT -- select existing products, mass-apply Update Stock /
 *    Change Price / Archive. Reached directly from the Products
 *    screen's own "Bulk Edit" shortcut.
 *
 * 2. IMPORT PRODUCTS -- the actual headline feature: a supplier who
 *    already has their whole stock in a spreadsheet uploads it once
 *    and publishes everything, rather than adding products one at a
 *    time. CSV/XLSX + a ZIP of images, real client-side parsing
 *    (services/parseSpreadsheet.ts, services/parseImageManifest.ts),
 *    validated against services/importColumns.ts's single source of
 *    truth for column names/order/requiredness. The full production
 *    design -- quarantine/scan/approve/publish media pipeline,
 *    DB-backed ImportJob progress (not just in-memory, since the
 *    existing background queue is a single in-process thread today),
 *    ZIP-bomb/path-traversal protection, tiered plan gating -- is
 *    captured for the backend build; this pass ships real, working
 *    Upload -> Preview, backend-ready but not yet backend-connected.
 */

import type { Cents, ProductCategory, ProductUnit } from "../products/types";

/**
 * Bulk price adjustment -- deliberately an ADJUSTMENT (percentage or
 * fixed delta), never a single absolute price applied across every
 * selected product. Selected products are rarely the same price
 * (Coke and Bread don't share a price), so "set all selected to
 * R12.00" would almost always be wrong; "increase all selected by 10%"
 * or "by R2.00" is the real supplier need ("my supplier's prices went
 * up, pass it on"), computed per-product against THAT product's own
 * current price -- see algorithms/priceAdjustment.ts.
 */
export type PriceAdjustmentDirection = "INCREASE" | "DECREASE";
export type PriceAdjustmentType = "PERCENTAGE" | "FIXED";

export interface PriceAdjustment {
  direction: PriceAdjustmentDirection;
  type: PriceAdjustmentType;
  /** Whole percentage points (10 = 10%) when type is PERCENTAGE;
   *  integer CENTS (same convention as products/types.ts's own Cents)
   *  when type is FIXED. Never a float, never rands directly -- the
   *  UI parses a typed rand value into cents the same way price entry
   *  already does (products/services/productMapper.ts's own
   *  parseCentsInput). */
  value: number;
}

// ---------------------------------------------------------------------------
// Import Products -- the actual "publish a whole spreadsheet of stock at
// once" feature. This is a genuinely different shape of work from Bulk
// Edit above (which only ever touches products that already exist):
// Import creates NEW products from a file the supplier already has.
//
// See services/importColumns.ts for the single source of truth on
// column names/order/requiredness -- the parser, the validator, the
// downloadable XLSX template, and the Word guide all read from that
// one file, so the four of them can never drift out of sync with each
// other.
// ---------------------------------------------------------------------------

export type ImportSourceType = "CSV" | "XLSX";

export interface ImportRowError {
  /** The column key this error belongs to (see importColumns.ts), or
   *  "_row" for an error that isn't specific to one column. */
  field: string;
  message: string;
}

/**
 * One parsed spreadsheet row. `raw` keeps the ORIGINAL string values
 * exactly as read -- never mutated -- so the preview can always show
 * the supplier exactly what was in their file, even for a row with
 * errors. The typed fields are only populated when that specific
 * field parsed/validated successfully; a row with `errors.length > 0`
 * will have some typed fields left null even though `raw` has a value
 * for them.
 */
export interface ParsedImportRow {
  /** 1-indexed as the supplier would see it if they opened the file in
   *  Excel themselves (row 1 = header, first data row = 2) -- matches
   *  how the error report needs to read ("Row 143: Invalid price"). */
  rowNumber: number;
  raw: Record<string, string>;
  name: string | null;
  category: ProductCategory | null;
  priceCents: Cents | null;
  sellingUnit: ProductUnit | null;
  /** How many the supplier currently has -- seeds the new product's
   *  real Inventory record on creation. Null only when the cell was
   *  genuinely invalid (not a number); a blank cell parses to 0, not
   *  null -- see importColumns.ts's own docstring for why a text
   *  "stock" status was retired in favour of this. */
  quantity: number | null;
  /** From image_1/image_2/image_3 columns, blanks dropped, ORDERED
   *  pairs of (which column, what filename) -- not a flat string[],
   *  because filtering out blank cells would otherwise make position
   *  meaningless (if image_1 is blank and image_2 isn't, a flat array
   *  loses which column the surviving value came from, and error
   *  messages need to say "image_2: not found", not just "not
   *  found"). Cross-referenced against the ZIP manifest separately
   *  (see ImportImageManifest) -- a filename appearing here doesn't by
   *  itself mean the image exists. */
  imageReferences: { column: string; filename: string }[];
  errors: ImportRowError[];
}

export interface ParsedImportFile {
  sourceType: ImportSourceType;
  fileName: string;
  rows: ParsedImportRow[];
  /** Every column header actually found in the file, in file order --
   *  used to build missingRequiredColumns/unrecognizedColumns below,
   *  and shown to the supplier directly if the whole file looks wrong
   *  (e.g. they uploaded something that isn't our template at all). */
  columnHeaders: string[];
  /** A header TRU Connect doesn't recognise (e.g. "pric" instead of
   *  "price") -- almost always a typo in the file, not an error in any
   *  one row, so it's surfaced once at the file level rather than
   *  repeated per row. */
  unrecognizedColumns: string[];
  /** A required column (see importColumns.ts) that wasn't found at
   *  all -- a whole-file problem ("this isn't the right template"),
   *  not something any per-row fix can solve. */
  missingRequiredColumns: string[];
}

/** Every image filename actually found inside the uploaded ZIP,
 *  exactly as it appears (basename only, folder prefixes stripped --
 *  a supplier zipping a folder of images typically gets `images/
 *  coke500.jpg` entries, and matching should ignore that folder). */
export interface ImportImageManifest {
  fileName: string;
  entries: string[];
}

export interface ImportPreviewSummary {
  totalRows: number;
  validRows: number;
  errorRows: number;
  totalImageReferences: number;
  matchedImages: number;
  missingImages: number;
}
