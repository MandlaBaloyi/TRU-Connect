import { UNIT_OPTIONS } from "@/features/dashboard/supplier/products/types";

/** The ProductUnit values that are units of MEASUREMENT rather than
 *  countable things. They keep their own casing and never take an "s"
 *  -- see describeMeasure. */
const MEASUREMENT_UNITS = new Set(["KG", "G", "L", "ML"]);

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

  return `${unit} of ${unitQuantity}${describeMeasure(unitMeasure, unitQuantity)}`;
}

/**
 * " bottles", " kg", or nothing at all.
 *
 * NAIVE PLURALISATION WAS A REAL, VISIBLE BUG: this used to append an
 * "s" to whatever the measure resolved to, which produced "Box of 20
 * eachs" on a supplier's own profile. Two separate problems, both
 * fixed here:
 *
 *   EACH IS NOT A MEASURE, it is the absence of one. "Box of 20" is
 *   already complete and correct; "Box of 20 eachs" is nonsense and
 *   "Box of 20 eaches" would be no better. It contributes nothing.
 *
 *   MEASUREMENT UNITS DO NOT PLURALISE. It is "10 kg", never "10 kgs";
 *   "2 L", never "2 Ls". Only countable things (bottles, cans,
 *   packets) take the s.
 */
function describeMeasure(unitMeasure: string | null | undefined, unitQuantity: number): string {
  if (!unitMeasure) return "";

  const raw = unitMeasure.toUpperCase();
  if (raw === "EACH") return "";

  // Symbols, not words -- kept in their own case ("kg", "L", "ml")
  // rather than lowercased, and never pluralised.
  if (MEASUREMENT_UNITS.has(raw)) return ` ${labelFor(unitMeasure)}`;

  const measure = labelFor(unitMeasure).toLowerCase();
  return ` ${measure}${unitQuantity === 1 ? "" : "s"}`;
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
