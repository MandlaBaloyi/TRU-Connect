/**
 * Field-level matchers for Import Products. Category and unit values
 * in the FILE are human-readable labels ("Beverages"), matched
 * case-insensitively against CATEGORY_OPTIONS/UNIT_OPTIONS' own
 * labels -- also accepting the raw internal code, so a supplier
 * re-uploading TRU Connect's own exported file still works. A genuine
 * miss is a clear per-row error ("Category not recognised"), never a
 * fuzzy best-guess match -- silently guessing wrong here would put a
 * product in the wrong category with no visible sign anything went
 * wrong.
 */

import { CATEGORY_OPTIONS, UNIT_OPTIONS } from "../../products/types";
import type { ProductCategory, ProductUnit } from "../../products/types";

function normalize(value: string): string {
  return value.trim().toLowerCase();
}

export function matchCategory(raw: string): ProductCategory | null {
  const q = normalize(raw);
  if (!q) return null;
  const byLabel = CATEGORY_OPTIONS.find((o) => o.label.toLowerCase() === q);
  if (byLabel) return byLabel.value;
  const byCode = CATEGORY_OPTIONS.find((o) => o.value.toLowerCase() === q);
  return byCode ? byCode.value : null;
}

export function matchUnit(raw: string): ProductUnit | null {
  const q = normalize(raw);
  if (!q) return null;
  const byLabel = UNIT_OPTIONS.find((o) => o.label.toLowerCase() === q);
  if (byLabel) return byLabel.value;
  const byCode = UNIT_OPTIONS.find((o) => o.value.toLowerCase() === q);
  return byCode ? byCode.value : null;
}
