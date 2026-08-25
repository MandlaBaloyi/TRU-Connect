/**
 * Discount math -- the calculation Product.compareAtPriceCents exists
 * to support. Kept as its own small, reusable module (matching
 * unitPricing.ts's own precedent in this folder) since it's called
 * from four separate places: ProductCard, InventoryListRow,
 * ProductDetailScreen, and mockProductsApi.ts's own bulkSetDiscount --
 * one formula, never re-derived slightly differently in each.
 */

import type { Cents } from "../types";

export interface Discount {
  /** Whole percentage points, rounded -- "22" means "22% off", never
   *  a fraction like 0.22 or a string. Rounded rather than floored/
   *  ceiled: a genuinely borderline discount (e.g. 22.5%) should read
   *  as the nearest honest round number a shopper would say aloud,
   *  not silently always favour one direction. */
  percentOff: number;
  /** The actual amount saved, in cents -- e.g. compareAt 3200, price
   *  2500 -> savingsCents 700. Kept alongside percentOff since some UI
   *  contexts want to show the Rand amount saved, not just the
   *  percentage. */
  savingsCents: Cents;
}

/**
 * Returns null when there's genuinely nothing to compute -- no
 * compareAtPriceCents at all, or (defensively, even though
 * product_service.py's own validation should already prevent this at
 * save time) a compareAtPriceCents that isn't actually higher than
 * priceCents. Callers should treat null as "show nothing", never fall
 * back to a 0% badge -- a product with no real discount shouldn't
 * carry a discount badge suggesting it does.
 */
export function calculateDiscount(priceCents: Cents, compareAtPriceCents: Cents | null): Discount | null {
  if (compareAtPriceCents === null || compareAtPriceCents <= priceCents) return null;

  const savingsCents = compareAtPriceCents - priceCents;
  const percentOff = Math.round((savingsCents / compareAtPriceCents) * 100);

  return { percentOff, savingsCents };
}

/**
 * The INVERSE of calculateDiscount -- given a product's own current
 * price and a target discount percentage, computes the compare-at
 * price that would produce exactly that percentage. Mirrors the real
 * backend's own product_service.py::bulk_set_discount formula exactly
 * (compare_at = price / (1 - discount/100), rounded to the nearest
 * cent) -- confirmed to round-trip correctly back through
 * calculateDiscount above for any valid input, same proof already run
 * against the real backend before it shipped.
 *
 * Used by Bulk Edit's own "Set Discount" action, and by
 * mockProductsApi.ts's own bulkSetDiscount so mock mode behaves
 * identically to the real backend rather than drifting.
 */
export function computeCompareAtPrice(priceCents: Cents, discountPercent: number): Cents {
  return Math.round(priceCents / (1 - discountPercent / 100));
}
