import { useCart } from "./useCart";
import { useSupplierProfile } from "../../find-supplier/hooks/useConnectionRequest";

/**
 * Who this order flow is with — name and avatar — for the social top
 * bar on the cart, order history and every checkout step.
 *
 * THE BUG THIS FIXES, reported directly: with an EMPTY cart those top
 * bars lost the supplier's name and photo and fell back to the plain
 * words "Cart" / "Order history".
 *
 * The cause is that all of them read the supplier off the cart, and
 * `getCart` genuinely returns NULL when no CART row exists (see the
 * comment in httpOrdersService.getCart — that null is deliberate and a
 * previous bug came from papering over it). So "the cart is empty" and
 * "we don't know who this supplier is" were the same state, which is
 * wrong: the supplier is perfectly well known. It bit hardest exactly
 * where it was least acceptable — order history is the screen a
 * business opens precisely when their cart is empty, and it lost the
 * identity of the supplier whose orders it was listing.
 *
 * RESOLUTION ORDER, cheapest first:
 *
 *   1. THE CART. Already loaded by every screen that calls this (same
 *      query key, so React Query dedupes and nothing extra is
 *      fetched). Carries both name and image. Answers whenever a cart
 *      exists at all.
 *   2. THE SUPPLIER PROFILE, requested ONLY when the cart could not
 *      answer. Usually already cached — a business reaches these
 *      screens through the supplier's brand profile or catalogue — and
 *      a single cheap fetch when it isn't.
 *   3. THE ROUTE PARAM the caller passed. Covers the first frame
 *      before either query resolves, and is name-only by nature. Same
 *      header-flash fix documented in business/routes.ts.
 *
 * NOT SOLVED BY MAKING THE BACKEND RETURN A CART SHELL. That would
 * mean inventing a cart that does not exist so a header could read a
 * name off it, and CartScreen's own empty state depends on that null
 * being honest. The screens were asking the wrong question, not
 * getting a wrong answer.
 */
export function useSupplierIdentity(supplierId: string, fallbackName?: string | null) {
  const { cart } = useCart(supplierId);

  const cartAnswered = Boolean(cart?.supplierName);
  const { data: profile } = useSupplierProfile(supplierId, { enabled: !cartAnswered });

  return {
    name: cart?.supplierName ?? profile?.businessName ?? fallbackName ?? null,
    photoUrl: cart?.supplierBusinessImageUrl ?? profile?.businessImageUrl ?? null,
    // THE THIRD THING EVERY HEADER NEEDS, alongside the name and the
    // photo. Same two sources in the same order: the cart answers when
    // there is one, the profile otherwise.
    verificationStatus:
      cart?.supplierVerificationStatus ?? profile?.verificationStatus ?? null,
  };
}
