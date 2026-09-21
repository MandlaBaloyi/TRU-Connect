import { apiGet } from "@/services/api/apiClient";

import type { FeedProduct, FeedSupplier } from "../types";

/**
 * The screens behind the feed's arrows.
 *
 * NO MOCK SWITCH, matching browseService's own reasoning: these
 * endpoints exist, and inventing a fake "everything you have ever
 * ordered" would mean designing against a history nobody has. An empty
 * real screen is a truer thing to look at than a full imaginary one.
 *
 * ONE SHAPE FOR ALL FIVE, because the server returns one shape. The
 * ranking is the server's -- deliberately the SAME ranking the rail
 * previewed (feed_detail_service on the backend), so a screen can never
 * disagree with the rail it opened from.
 *
 * PAGING IS OFFSET-BASED rather than cursor-based, because these lists
 * are short enough to hold in memory and stable within a session: a
 * shop's order history does not reshuffle while they scroll it. Moving
 * fast is the one that genuinely changes underneath, and it is
 * recomputed on each fetch rather than pinned, which is the honest
 * behaviour for a screen whose whole claim is "right now".
 */

/** The narrowing every see-all screen shares. The four screens are one
 *  screen with different data, so they take one set of controls. */
export interface SeeAllControls {
  search?: string;
  /** "relevance" means LEAVE THE ORDER ALONE. Each of these lists
   *  arrives ranked by something that took work — most recently
   *  ordered, most tapped, fastest rising — and that ranking is the
   *  rail's whole argument. Alphabetising it by default would throw
   *  away the reason the reader tapped through. */
  sort?: "relevance" | "price_asc" | "price_desc" | "name";
  supplier?: string | null;
}

export interface ProductPage {
  products: FeedProduct[];
  hasMore: boolean;
  total: number;
  /** Who is selling in THIS list, with counts. First page only — they
   *  do not change as you scroll. */
  suppliers?: { id: string; name: string; count: number }[];
}

export interface SupplierPage {
  suppliers: FeedSupplier[];
  hasMore: boolean;
  total: number;
}

async function productPage(
  path: string,
  offset: number,
  controls: SeeAllControls = {}
): Promise<ProductPage> {
  const query = new URLSearchParams({ offset: String(offset) });
  if (controls.search) query.set("search", controls.search);
  // RELEVANCE IS THE SERVER'S DEFAULT, so it is not sent. Every
  // parameter omitted is one fewer thing that can disagree.
  if (controls.sort && controls.sort !== "relevance") query.set("sort", controls.sort);
  if (controls.supplier) query.set("supplier", controls.supplier);

  const data = await apiGet<ProductPage>(`${path}?${query.toString()}`);
  return {
    products: data?.products ?? [],
    hasMore: data?.hasMore ?? false,
    total: data?.total ?? 0,
    // ABSENT ON LATER PAGES BY DESIGN, not missing. The hook reads
    // these off the FIRST page only.
    suppliers: data?.suppliers,
  };
}

async function supplierPage(path: string, offset: number): Promise<SupplierPage> {
  const data = await apiGet<SupplierPage>(`${path}?offset=${offset}`);
  return {
    suppliers: data?.suppliers ?? [],
    hasMore: data?.hasMore ?? false,
    total: data?.total ?? 0,
  };
}

export const getBuyItAgain = (offset = 0, controls?: SeeAllControls) =>
  productPage("/community/buy-it-again", offset, controls);

export const getMovingFast = (offset = 0, controls?: SeeAllControls) =>
  productPage("/community/moving-fast", offset, controls);

/** Everything this shop opened and never ordered. The only see-all here
 *  built on the impressions table rather than on orders, declarations
 *  or the market — and so the only one that empties as they buy. */
export const getLeftOff = (offset = 0, controls?: SeeAllControls) =>
  productPage("/community/left-off", offset, controls);

export const getStockForYou = (offset = 0, controls?: SeeAllControls) =>
  productPage("/community/stock-for-you", offset, controls);

export const getCollectNearYou = (offset = 0) =>
  supplierPage("/community/collect-near-you", offset);

export const getNotOrderedYet = (offset = 0) =>
  supplierPage("/community/not-ordered-yet", offset);
