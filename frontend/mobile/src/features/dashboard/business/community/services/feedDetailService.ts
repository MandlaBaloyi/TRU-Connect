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

export interface ProductPage {
  products: FeedProduct[];
  hasMore: boolean;
  total: number;
}

export interface SupplierPage {
  suppliers: FeedSupplier[];
  hasMore: boolean;
  total: number;
}

async function productPage(path: string, offset: number): Promise<ProductPage> {
  const data = await apiGet<ProductPage>(`${path}?offset=${offset}`);
  return {
    products: data?.products ?? [],
    hasMore: data?.hasMore ?? false,
    total: data?.total ?? 0,
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

export const getBuyItAgain = (offset = 0) =>
  productPage("/community/buy-it-again", offset);

export const getMovingFast = (offset = 0) =>
  productPage("/community/moving-fast", offset);

export const getStockForYou = (offset = 0) =>
  productPage("/community/stock-for-you", offset);

export const getCollectNearYou = (offset = 0) =>
  supplierPage("/community/collect-near-you", offset);

export const getNotOrderedYet = (offset = 0) =>
  supplierPage("/community/not-ordered-yet", offset);
