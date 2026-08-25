/**
 * validateRow — one raw spreadsheet row in, one ParsedImportRow out.
 * Collects EVERY field error on the row, not just the first one hit --
 * a supplier fixing errors one CSV upload at a time because each pass
 * only revealed one problem per row would be a genuinely bad
 * experience for exactly the "I have 2,000 products" case this
 * feature exists for.
 */

import type { ImportRowError, ParsedImportRow } from "../types";
import type { Cents } from "../../products/types";
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

  // sku/description/compare_at_price are ALL optional -- same "leave
  // it blank if you don't need it" pattern as quantity and the image
  // columns. sku's own uniqueness is checked later, server-side, when
  // the row actually reaches product_service.create_product -- this
  // validator (matching the backend's own row_validator.py exactly)
  // only checks shape here.
  const skuRaw = (raw.sku ?? "").trim();
  const sku = skuRaw || null;

  const descriptionRaw = (raw.description ?? "").trim();
  const description = descriptionRaw || null;

  const compareAtPriceRaw = (raw.compare_at_price ?? "").trim();
  let compareAtPriceCents: Cents | null = null;
  if (compareAtPriceRaw) {
    compareAtPriceCents = parseCentsInput(compareAtPriceRaw);
    if (compareAtPriceCents === null) {
      errors.push({ field: "compare_at_price", message: `Invalid compare-at price: "${compareAtPriceRaw}".` });
    } else if (priceCents !== null && compareAtPriceCents <= priceCents) {
      // Same rule as the single-product form's own validation
      // (product_service.py on the backend) -- caught here too so a
      // supplier sees this in the PREVIEW, before ever submitting.
      errors.push({
        field: "compare_at_price",
        message: "Compare-at price must be higher than the actual price to show as a discount.",
      });
    }
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
    sku,
    description,
    compareAtPriceCents,
    imageReferences,
    errors,
  };
}
