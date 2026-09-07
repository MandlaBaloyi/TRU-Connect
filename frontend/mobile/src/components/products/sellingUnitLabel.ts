import { UNIT_OPTIONS } from "@/features/dashboard/supplier/products/types";
import { describeUnit } from "./unitEconomics";

/**
 * "per case", "per bottle" — the unit a price is quoted in.
 *
 * WHY THIS MATTERS ENOUGH TO SHOW ON EVERY CARD: a bare "R240.00" is
 * unusable for a wholesale decision. A case of 24 and a single bottle
 * at the same price are completely different offers, and an informal
 * business comparing suppliers is really comparing unit economics.
 * sellingUnit was in the payload from the start and rendered nowhere.
 *
 * Returns null for EACH: "per each" is not English, and a single item
 * is the assumed default anyway — saying nothing is the correct output,
 * not a fallback.
 */
export function sellingUnitLabel(
  sellingUnit: string | null | undefined,
  unitQuantity?: number | null,
  unitMeasure?: string | null
): string | null {
  if (!sellingUnit || (sellingUnit === "EACH" && !unitQuantity)) return null;

  // Prefer the FULL description when the pack contents are known --
  // "Pack of 6 bottles" answers what "per pack" only gestures at.
  const described = describeUnit(sellingUnit, unitQuantity, unitMeasure);
  if (described && unitQuantity && unitQuantity > 1) return described;

  const label = UNIT_OPTIONS.find((option) => option.value === sellingUnit)?.label;
  return label ? `per ${label.toLowerCase()}` : null;
}
