/**
 * Unit pricing math -- the calculation Product.unitQuantity/unitMeasure
 * exist to support (see types.ts's own docstring on those fields).
 *
 * NOT WIRED TO ANY SCREEN YET, deliberately -- Add Product doesn't
 * collect unitQuantity/unitMeasure in this pass, so there's nothing
 * for a screen to call this with yet. Written now, alongside the
 * schema fields it depends on, so the UI work that eventually surfaces
 * "R120 / case = R5.00 per bottle" has real, already-tested math to
 * call rather than inventing it under time pressure later.
 */

import type { Cents } from "../types";

/**
 * "1 Case = 24 bottles, R120" -> "R5.00 per bottle". Returns null when
 * there's nothing to divide by (unitQuantity missing, zero, or
 * negative) -- callers should treat null as "show nothing", never
 * fall back to displaying the sellingUnit price as if it were the
 * per-base-unit price.
 */
export function computeUnitPriceCents(priceCents: Cents, unitQuantity: number | null): Cents | null {
  if (unitQuantity === null || !Number.isFinite(unitQuantity) || unitQuantity <= 0) return null;
  return Math.round(priceCents / unitQuantity);
}
