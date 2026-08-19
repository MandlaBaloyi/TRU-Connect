/**
 * validateRow — one raw spreadsheet row in, one ParsedImportRow out.
 * Collects EVERY field error on the row, not just the first one hit --
 * a supplier fixing errors one CSV upload at a time because each pass
 * only revealed one problem per row would be a genuinely bad
 * experience for exactly the "I have 2,000 products" case this
 * feature exists for.
 */

import type { ImportRowError, ParsedImportRow } from "../types";
import { IMAGE_COLUMN_HEADERS } from "./importColumns";
import { matchCategory, matchUnit } from "./importMatchers";
import { parseCentsInput } from "../../products/services/productMapper";

/**
 * Parses the quantity cell -- blank means 0 (a brand-new product with
 * no stock yet is a normal, valid state, not an error), anything
 * present must be a non-negative whole number. Never a float -- stock
 * counts are always whole units.
 */
function parseQuantity(raw: string): { value: number | null; error: string | null } {
  const trimmed = raw.trim();
  if (!trimmed) return { value: 0, error: null };
  if (!/^\d+$/.test(trimmed)) {
    return { value: null, error: `Invalid quantity: "${raw}". Use a whole number, e.g. 50.` };
  }
  return { value: Number.parseInt(trimmed, 10), error: null };
}

export function validateRow(raw: Record<string, string>, rowNumber: number): ParsedImportRow {
  const errors: ImportRowError[] = [];

  const nameRaw = raw.name ?? "";
  const name = nameRaw.trim() || null;
  if (!name) errors.push({ field: "name", message: "Product name is required." });

  const category = matchCategory(raw.category ?? "");
  if (!category) {
    errors.push({
      field: "category",
      message: raw.category ? `Category not recognised: "${raw.category}".` : "Category is required.",
    });
  }

  const priceCents = parseCentsInput(raw.price ?? "");
  if (priceCents === null) {
    errors.push({
      field: "price",
      message: raw.price ? `Invalid price: "${raw.price}".` : "Price is required.",
    });
  }

  const sellingUnit = matchUnit(raw.unit ?? "");
  if (!sellingUnit) {
    errors.push({
      field: "unit",
      message: raw.unit ? `Unit not recognised: "${raw.unit}".` : "Unit is required.",
    });
  }

  const quantityResult = parseQuantity(raw.quantity ?? "");
  if (quantityResult.error) {
    errors.push({ field: "quantity", message: quantityResult.error });
  }

  const imageReferences = IMAGE_COLUMN_HEADERS.map((column) => ({ column, filename: (raw[column] ?? "").trim() }))
    .filter((ref) => ref.filename.length > 0);

  return {
    rowNumber,
    raw,
    name,
    category,
    priceCents,
    sellingUnit,
    quantity: quantityResult.value,
    imageReferences,
    errors,
  };
}
