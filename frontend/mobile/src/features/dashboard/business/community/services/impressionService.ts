import { apiPost } from "@/services/api/apiClient";

/**
 * Telling the server what was tapped.
 *
 * THE ONLY HALF THE DEVICE IS TRUSTED FOR. What the feed DELIVERED is
 * counted server-side at compose time — the composer already knows
 * exactly what it returned, so there is no round trip and no double
 * counting when a screen re-renders. A tap is the one thing only this
 * device witnesses, which is why it is the one thing it may assert.
 *
 * BATCHED, AND THE BATCHING IS NOT AN OPTIMISATION. The endpoint is
 * rate limited per minute, so one POST per tap would make a shopkeeper
 * scrolling hard hit a 429 on their own feed. useTapTracking collects
 * and flushes; this file only knows how to send what it is handed.
 *
 * IT NEVER THROWS AT THE CALLER. A lost counter is a lost counter. A
 * feed that shows an error because analytics failed is a feed that has
 * forgotten what it is for — the measurement serves the product, and a
 * product that breaks for its own telemetry has the relationship
 * backwards.
 */

export type ImpressionItemType = "PRODUCT" | "SUPPLIER" | "CATEGORY";

export interface FeedTap {
  /** The section id the server used — "buy-it-again". */
  rail: string;
  /** Zero-based index WITHIN that rail, not across the feed. The
   *  server's whole reason for storing it is comparing position 0 to
   *  position 1 of the same row. */
  position: number;
  itemId: string;
  itemType: ImpressionItemType;
  /** Who would be billed, when the sponsored slot is sold. Absent for
   *  a category chip, which names nobody. */
  supplierId?: string | null;
}

/** Matches MAX_TAPS_PER_REQUEST on the server. Kept in step by hand:
 *  the server refuses a larger batch with a 422, so the failure is
 *  loud rather than silent if these ever drift. */
export const MAX_TAPS_PER_REQUEST = 100;

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

export async function sendTaps(taps: FeedTap[]): Promise<void> {
  if (taps.length === 0) return;

  // NOTHING IS SENT IN MOCK MODE. There is no server to receive it,
  // and a 404 on every scroll would train everyone to ignore the
  // console — which is the state that hides the next real error.
  if (USE_MOCK) return;

  try {
    await apiPost("/community/impressions/tap", {
      taps: taps.slice(0, MAX_TAPS_PER_REQUEST),
    });
  } catch {
    // SWALLOWED ON PURPOSE. See the module docstring: the caller is a
    // feed, and the feed's job does not depend on this succeeding.
  }
}
