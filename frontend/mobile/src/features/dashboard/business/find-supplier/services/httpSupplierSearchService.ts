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
import type { ConnectionStatus, SupplierProduct, SupplierProfilePreview, SupplierSearchResult } from "../types";

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

export async function inviteSupplier(email: string): Promise<{ status: "SENT" }> {
  return apiPost<{ status: "SENT" }>("/supplier-discovery/invitations", { email });
}

export async function getSupplierProducts(supplierId: string): Promise<SupplierProduct[]> {
  const data = await apiGet<{ products: SupplierProduct[] }>(`/supplier-discovery/suppliers/${supplierId}/products`);
  return data.products;
}
