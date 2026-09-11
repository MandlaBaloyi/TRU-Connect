import { formatCents } from "@/features/dashboard/supplier/products/services/productMapper";
import type { FeedSupplier } from "../../types";

/**
 * The one line under a supplier's name on every card, built in one
 * place so no two cards ever describe the same supplier differently.
 *
 * WHAT IT DELIBERATELY DOES NOT CONTAIN. The apps this screen borrows
 * its shape from lead with "4.4 ★ (15,000+) · 11 min". TruConnect has
 * neither number and must not invent them:
 *
 *   * There are no reviews, by decision rather than omission -- the
 *     whole track-record model was built on figures that cannot be
 *     gamed the way a star rating invites.
 *   * Nothing records delivery, so a "25 min" badge would be fiction.
 *     That is the same gap the "orders fulfilled" tile is honest about.
 *
 * WHAT IT DOES CONTAIN is arguably more useful to someone buying
 * stock: can they bring it, what does it take to order, and are they
 * around. All four are real fields already on the payload.
 *
 * ORDER MATTERS, most decisive first. "Delivers" or "Collection only"
 * is the answer that can rule a supplier out entirely for a business
 * without transport; the minimum can rule out today's order; distance
 * is context. A count of connections is social proof and goes last.
 *
 * NULL IS NOT FALSE, for delivery. A supplier who has never stated
 * their terms shows nothing here -- never "Collection only", which
 * would put words in their mouth. Same tri-state rule the checkout
 * enforces (see offers_delivery's own column comment).
 */
export function supplierMetaLine(supplier: FeedSupplier): string {
  const parts: string[] = [];

  if (supplier.offersDelivery === true) parts.push("Delivers");
  else if (supplier.offersDelivery === false) parts.push("Collection only");

  if (supplier.minimumOrderCents !== null) {
    parts.push(`Min ${formatCents(supplier.minimumOrderCents)}`);
  }

  if (supplier.distanceKm !== null) {
    // One decimal under 10km, whole numbers above -- "12.5 km away" is
    // false precision for a trip somebody drives, but the difference
    // between 2.1 and 2.8 genuinely changes the decision.
    const distance = supplier.distanceKm < 10 ? supplier.distanceKm.toFixed(1) : Math.round(supplier.distanceKm);
    parts.push(`${distance} km`);
  }

  if (supplier.connectedBusinessCount > 0) {
    parts.push(
      supplier.connectedBusinessCount === 1
        ? "1 business connected"
        : `${supplier.connectedBusinessCount} businesses connected`
    );
  }

  return parts.join(" · ");
}
