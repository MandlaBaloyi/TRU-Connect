import { apiGet } from "@/services/api/apiClient";
import type { BrowseFilters, BrowseResult } from "../types";

/**
 * The browse feature's only data boundary — same rule every other
 * feature here follows.
 *
 * NO MOCK SWITCH. Unlike the older services there is no mock
 * implementation to fall back to: this endpoint exists, and inventing a
 * fake catalogue would mean designing against stock that cannot be
 * bought. An empty real catalogue is a truer thing to look at than a
 * full imaginary one.
 */
export async function browseCategory(
  params: BrowseFilters & { category?: string; limit?: number; offset?: number }
): Promise<BrowseResult> {
  const query = new URLSearchParams();
  if (params.category) query.set("category", params.category);
  if (params.search) query.set("search", params.search);
  if (params.kind) query.set("kind", params.kind);
  if (params.supplier) query.set("supplier", params.supplier);
  if (params.mineOnly) query.set("mine", "true");
  // NAME IS THE SERVER'S DEFAULT, so it is not sent. Every parameter
  // omitted is one fewer thing that can disagree between the two sides.
  if (params.sort && params.sort !== "name") query.set("sort", params.sort);
  if (params.limit) query.set("limit", String(params.limit));
  if (params.offset) query.set("offset", String(params.offset));

  const data = await apiGet<BrowseResult>(`/catalogue/browse?${query.toString()}`);
  return {
    products: data?.products ?? [],
    hasMore: data?.hasMore ?? false,
    // ABSENT ON LATER PAGES BY DESIGN, not missing. useCategoryBrowse
    // reads these off the FIRST page only.
    total: data?.total,
    kinds: data?.kinds,
    suppliers: data?.suppliers,
  };
}
