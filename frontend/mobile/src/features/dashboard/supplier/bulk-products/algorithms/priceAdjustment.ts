/**
 * Bulk price adjustment math. Applied PER-PRODUCT against that
 * product's own current price -- see types.ts's own PriceAdjustment
 * docstring for why this is a delta, never a shared absolute price
 * across a mixed selection.
 */

import type { Cents } from "../../products/types";
import type { PriceAdjustment } from "../types";

/**
 * Never returns a negative price -- a DECREASE larger than the
 * product's own price clamps to 0, it doesn't go negative. Rounds to
 * the nearest cent (percentage math can produce fractional cents;
 * money is always a whole number of cents everywhere in this app).
 */
export function applyPriceAdjustment(priceCents: Cents, adjustment: PriceAdjustment): Cents {
  const delta =
    adjustment.type === "PERCENTAGE" ? Math.round(priceCents * (adjustment.value / 100)) : adjustment.value;

  const adjusted = adjustment.direction === "INCREASE" ? priceCents + delta : priceCents - delta;
  return Math.max(0, adjusted);
}
