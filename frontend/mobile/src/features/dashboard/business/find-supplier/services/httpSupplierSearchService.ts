/**
 * Supplier search service, REAL HTTP implementation — calls the
 * actual /api/v1/supplier-discovery/* endpoints (see backend's
 * src/domains/network/supplier_discovery/api/supplier_discovery_routes.py).
 * Selected by services/supplierSearchService.ts when
 * EXPO_PUBLIC_USE_MOCK_API=false, same split as
 * business-profile/api/httpBusinessProfileApi.ts.
 *
 * Response shapes match types.ts's SupplierSearchResult/
 * SupplierProfilePreview FIELD-FOR-FIELD — the backend's own
 * to_search_result_dict/to_profile_preview_dict methods
 * (supplier_profile.py) were deliberately written to produce exactly
 * this camelCase shape, so no field-mapping layer exists here on
 * purpose. If the two ever drift, that's a contract break to fix at
 * the source, not paper over with a mapper in this file.
 *
 * apiGet/apiPost already unwrap the {success, message, data} envelope
 * and attach the caller's stored JWT — see services/api/apiClient.ts.
 * Paths here are relative to API_BASE_URL, which already includes
 * /api/v1 (constants/config.ts) — never repeat that prefix here.
 */
import { apiGet, apiPost, ApiError } from "@/services/api/apiClient";

import { recordRecentlyViewed } from "./recentSearchesStore";
import type {
  ConnectionStatus,
  DisconnectReason,
  ReportReason,
  SupplierProduct,
  SupplierProductDetail,
  SupplierProductsCatalog,
  SupplierProductsQuery,
  SupplierProfilePreview,
  SupplierSearchResult,
  SupplierShowcase,
} from "../types";

export async function searchSuppliers(query: string): Promise<SupplierSearchResult[]> {
  const data = await apiGet<{ results: SupplierSearchResult[] }>(
    `/supplier-discovery/search?q=${encodeURIComponent(query)}`
  );
  return data.results;
}

export async function getSupplierProfile(id: string): Promise<SupplierProfilePreview | null> {
  try {
    const profile = await apiGet<SupplierProfilePreview>(`/supplier-discovery/suppliers/${id}`);
    recordRecentlyViewed({ id: profile.id, businessName: profile.businessName });
    return profile;
  } catch (error) {
    // SUPPLIER_NOT_FOUND -> null, matching the mock implementation's
    // contract exactly (the screen already renders ErrorState for
    // null) — every OTHER error (network, 500, etc.) still propagates,
    // since those aren't "this supplier doesn't exist", they're "we
    // couldn't find out".
    if (error instanceof ApiError && error.code === "SUPPLIER_NOT_FOUND") {
      return null;
    }
    throw error;
  }
}

export async function requestConnection(supplierId: string): Promise<ConnectionStatus> {
  const data = await apiPost<{ connectionStatus: ConnectionStatus }>(
    `/supplier-discovery/suppliers/${supplierId}/connection-requests`
  );
  return data.connectionStatus;
}

export async function endConnection(
  supplierId: string,
  reason: DisconnectReason,
  details: string | null
): Promise<void> {
  await apiPost(`/supplier-discovery/suppliers/${supplierId}/disconnect`, { reason, details });
}

export async function reportSupplier(
  supplierId: string,
  reason: ReportReason,
  details: string | null,
  productId?: string
): Promise<void> {
  await apiPost(`/supplier-discovery/suppliers/${supplierId}/report`, { reason, details, product_id: productId });
}

export async function inviteSupplier(email: string): Promise<{ status: "SENT" }> {
  return apiPost<{ status: "SENT" }>("/supplier-discovery/invitations", { email });
}

/** The brand-profile product showcase -- the supplier's real product
 *  categories (biggest first, max 5), each a strip. Imageless products
 *  excluded, pinned products first within their category (see backend
 *  connections_service.list_profile_products / _group_profile_showcase). */
export async function getSupplierProfileProducts(supplierId: string): Promise<SupplierShowcase> {
  return apiGet<SupplierShowcase>(`/supplier-discovery/suppliers/${supplierId}/profile-products`);
}

export async function getSupplierProducts(
  supplierId: string,
  query: SupplierProductsQuery = {}
): Promise<SupplierProductsCatalog> {
  return apiGet<SupplierProductsCatalog>(`/supplier-discovery/suppliers/${supplierId}/products`, {
    params: {
      page: query.page,
      limit: query.limit,
      sort: query.sort,
      category: query.category ?? undefined,
    },
  });
}

/** The real fix for a real bug: this used to be derived on the
 *  frontend from whichever products happened to be on the currently-
 *  loaded page, which broke the moment pagination existed (the option
 *  list would shift depending on which page you were viewing). A
 *  dedicated endpoint -- correct regardless of page/sort/filter,
 *  fetched once rather than recomputed on every page change. */
export async function getSupplierProductCategories(supplierId: string): Promise<string[]> {
  const data = await apiGet<{ categories: string[] }>(`/supplier-discovery/suppliers/${supplierId}/products/categories`);
  return data.categories;
}

export async function getSupplierProduct(
  supplierId: string,
  productId: string
): Promise<SupplierProductDetail | null> {
  try {
    return await apiGet<SupplierProductDetail>(
      `/supplier-discovery/suppliers/${supplierId}/products/${productId}`
    );
  } catch (error) {
    // PRODUCT_NOT_FOUND -> null, same contract as getSupplierProfile's
    // own SUPPLIER_NOT_FOUND handling just above -- every OTHER error
    // still propagates.
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      return null;
    }
    throw error;
  }
}

/** "More from [Supplier]" -- same supplier, same category, excludes
 *  the product being viewed, capped at 5. Genuinely zero or one
 *  result when that's all that matches -- see the real backend's own
 *  list_related_products docstring on why the criteria is never
 *  widened just to force a count. */
export async function getRelatedProducts(supplierId: string, productId: string): Promise<SupplierProduct[]> {
  const data = await apiGet<{ products: SupplierProduct[] }>(
    `/supplier-discovery/suppliers/${supplierId}/products/${productId}/related`
  );
  return data.products;
}
