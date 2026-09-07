import { UNIT_OPTIONS } from "@/features/dashboard/supplier/products/types";

/**
 * How a wholesale price is actually read: what's in the pack, and what
 * that works out to per item.
 *
 * WHY THIS MATTERS MORE THAN IT LOOKS — "Sold as: Pack" was all a
 * business ever saw, because unit_quantity and unit_measure existed on
 * the product model and were never sent to them. A pack of 6 and a pack
 * of 24 at the same price are completely different offers, and an
 * informal buyer comparing two suppliers is really comparing per-item
 * cost. Doing that arithmetic in your head, in a shop, from two phone
 * screens, is exactly the friction this removes.
 */

/** "Pack of 6 bottles", "Box of 12", "Each" — the human phrase for what
 *  one purchase actually contains. */
export function describeUnit(
  sellingUnit: string | null | undefined,
  unitQuantity: number | null | undefined,
  unitMeasure: string | null | undefined
): string | null {
  if (!sellingUnit) return null;
  const unit = labelFor(sellingUnit);

  // Nothing more to say than the unit itself: no quantity recorded, or
  // a quantity of 1 (a "Pack of 1" is just a pack).
  if (!unitQuantity || unitQuantity <= 1) return unit;

  const measure = unitMeasure ? labelFor(unitMeasure).toLowerCase() : null;
  const plural = measure ? `${measure}${unitQuantity === 1 ? "" : "s"}` : null;
  return plural ? `${unit} of ${unitQuantity} ${plural}` : `${unit} of ${unitQuantity}`;
}

/**
 * Cents per individual item, or null when there's nothing meaningful to
 * divide by.
 *
 * Returns null rather than the pack price for a quantity of 1 — showing
 * "R200.00 each" beneath a R200.00 pack price is noise that implies a
 * calculation happened when none did.
 */
export function perUnitCents(
  priceCents: number,
  unitQuantity: number | null | undefined
): number | null {
  if (!unitQuantity || unitQuantity <= 1) return null;
  return Math.round(priceCents / unitQuantity);
}

function labelFor(value: string): string {
  return UNIT_OPTIONS.find((option) => option.value === value)?.label ?? value;
}
