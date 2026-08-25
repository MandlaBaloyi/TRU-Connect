/**
 * pendingPhotoPolling.ts — the shared heuristic behind the automatic
 * refetch useProducts/useProduct now do after a photo upload.
 *
 * WHY THIS EXISTS: a freshly uploaded photo doesn't appear in
 * Product.images until Cloudinary's real scan finishes and our
 * backend's webhook applies the result -- confirmed via real device
 * testing to typically take 20-45 seconds. Before this, the app only
 * ever learned about that change when the user manually refreshed
 * (pull-to-refresh, or reopening the screen) -- this makes it check
 * on its own, briefly, right when it actually matters.
 *
 * THE HEURISTIC, DELIBERATELY SIMPLE -- a product counts as "possibly
 * still waiting on a photo" if it has NO approved images yet AND was
 * created within the last POLL_WINDOW_MS. No new backend endpoint, no
 * cross-screen "watch list" state to build or maintain -- just the
 * two fields every product response already carries (images,
 * createdAt).
 *
 * SELF-LIMITING ON BOTH ENDS -- once a photo is approved,
 * images.length becomes > 0 and polling stops on its own (React Query
 * re-evaluates refetchInterval every time fresh data arrives, so this
 * needs no manual cleanup). Once POLL_WINDOW_MS passes since creation,
 * polling stops even if no photo ever resolves (e.g. the supplier
 * never attached one, or it genuinely failed) -- this never polls
 * forever.
 *
 * ONE KNOWN, ACCEPTED TRADEOFF -- a product created with NO photo
 * intended at all still gets polled for the same window, since
 * images.length === 0 alone can't distinguish "nothing was ever
 * uploaded" from "something was uploaded, not approved yet" without a
 * real pending-upload tracking mechanism. A handful of harmless extra
 * fetches for up to POLL_WINDOW_MS is a reasonable cost for not
 * needing that extra machinery -- revisit only if it turns out to
 * matter in practice.
 */
import type { Product } from "../types";

const POLL_WINDOW_MS = 90_000; // ~90s -- covers the real 20-45s scan times observed, plus headroom
const POLL_INTERVAL_MS = 3_000;

function isRecentlyCreatedWithNoApprovedImages(product: Product): boolean {
  if (product.images.length > 0) return false;
  const ageMs = Date.now() - new Date(product.createdAt).getTime();
  return ageMs >= 0 && ageMs < POLL_WINDOW_MS;
}

/** For useProduct -- a single product's own detail view. */
export function pollIntervalForProduct(product: Product | undefined): number | false {
  if (!product) return false;
  return isRecentlyCreatedWithNoApprovedImages(product) ? POLL_INTERVAL_MS : false;
}

/** For useProducts -- polls if ANY product in the currently loaded
 *  list is still possibly waiting on a photo, so a supplier watching
 *  the list (exactly the real scenario this was built from) sees it
 *  resolve without needing to pull to refresh. */
export function pollIntervalForProductList(products: Product[]): number | false {
  return products.some(isRecentlyCreatedWithNoApprovedImages) ? POLL_INTERVAL_MS : false;
}
