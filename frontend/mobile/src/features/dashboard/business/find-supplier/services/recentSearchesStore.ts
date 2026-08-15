/**
 * Recently viewed suppliers — a pure local UX convenience, not backend
 * data (there is no /supplier-discovery/recent-searches endpoint, and
 * there was never meant to be one — see this feature's own PR history:
 * this was designed from the start as "recently viewed", not
 * server-tracked search history). Independent of USE_MOCK_API on
 * purpose: switching between mock and real search data shouldn't also
 * silently change whether "recently viewed" works.
 *
 * Session-scoped, in-memory, resets on app restart — same reasoning as
 * every other genuinely-local, non-authoritative piece of state in
 * this app (see my-account/services/accountService.ts's own docstring
 * for the identical argument against persisting things like this to
 * AsyncStorage: it isn't account data the backend will ever own, so
 * pretending a local save is durable would misrepresent that).
 */

const RECENT_SEARCHES_LIMIT = 5;
let recentlyViewed: { id: string; businessName: string }[] = [];

export function recordRecentlyViewed(supplier: { id: string; businessName: string }): void {
  recentlyViewed = [supplier, ...recentlyViewed.filter((s) => s.id !== supplier.id)].slice(
    0,
    RECENT_SEARCHES_LIMIT
  );
}

export async function getRecentSearches(): Promise<{ id: string; businessName: string }[]> {
  return recentlyViewed;
}
