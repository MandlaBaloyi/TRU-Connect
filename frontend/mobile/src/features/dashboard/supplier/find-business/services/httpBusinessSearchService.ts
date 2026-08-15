/**
 * Business search service, REAL HTTP implementation — calls the
 * actual /api/v1/supplier-discovery/businesses/* endpoints, verified
 * end-to-end against real Postgres before this file was written (see
 * this feature's own types.ts backend-contract note). Selected by
 * services/businessSearchService.ts when EXPO_PUBLIC_USE_MOCK_API=false.
 *
 * Response shapes match types.ts's BusinessSearchResult/
 * BusinessProfilePreview field-for-field — confirmed directly against
 * BusinessProfile.to_search_result_dict/to_profile_preview_dict, not
 * assumed.
 */
import { apiGet, apiPost, ApiError } from "@/services/api/apiClient";

import { recordRecentlyViewed } from "./recentSearchesStore";
import type { BusinessProfilePreview, BusinessSearchResult, ConnectionStatus } from "../types";

export async function searchBusinesses(query: string): Promise<BusinessSearchResult[]> {
  const data = await apiGet<{ results: BusinessSearchResult[] }>(
    `/supplier-discovery/businesses/search?q=${encodeURIComponent(query)}`
  );
  return data.results;
}

export async function getBusinessProfile(id: string): Promise<BusinessProfilePreview | null> {
  try {
    const profile = await apiGet<BusinessProfilePreview>(`/supplier-discovery/businesses/${id}`);
    recordRecentlyViewed({ id: profile.id, businessName: profile.businessName });
    return profile;
  } catch (error) {
    // BUSINESS_NOT_FOUND -> null, matching the mock implementation's
    // contract exactly — every OTHER error still propagates.
    if (error instanceof ApiError && error.code === "BUSINESS_NOT_FOUND") {
      return null;
    }
    throw error;
  }
}

export async function requestConnection(businessId: string): Promise<ConnectionStatus> {
  const data = await apiPost<{ connectionStatus: ConnectionStatus }>(
    `/supplier-discovery/businesses/${businessId}/connection-requests`
  );
  return data.connectionStatus;
}

export async function inviteBusiness(email: string): Promise<{ status: "SENT" }> {
  return apiPost<{ status: "SENT" }>("/supplier-discovery/business-invitations", { email });
}
