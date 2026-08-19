/**
 * Business search service — mock implementation. Mirrors
 * business/find-supplier/services/mockSupplierSearchService.ts
 * exactly, minus verificationStatus (BusinessProfile's real
 * to_search_result_dict/to_profile_preview_dict don't return one —
 * verified directly against those methods, see this feature's own
 * types.ts).
 *
 * SEARCH IS NAME/BUSINESS-NAME PREFIX MATCH ONLY, mirroring the real
 * backend exactly (BusinessProfileRepository.search_by_name_prefix) —
 * phone/email exact-match search was removed (see types.ts's own file
 * header), and this mock's matching logic was also changed from a
 * substring `.includes()` scan to a genuine prefix match, for the
 * same reason as the Find Supplier mock's own identical change.
 */
import type { BusinessProfilePreview, BusinessSearchResult, ConnectionStatus } from "../types";
import { recordRecentlyViewed } from "./recentSearchesStore";

const latency = (ms = 500) => new Promise<void>((resolve) => setTimeout(resolve, ms));

interface MockBusiness {
  id: string;
  businessName: string;
  category: string;
  location: string;
  memberSinceYear: number;
  description: string;
  photoUrl: string | null;
}

const MOCK_BUSINESSES: MockBusiness[] = [
  {
    id: "biz_001",
    businessName: "Mandla's Spaza Shop",
    category: "Retail",
    location: "Polokwane",
    memberSinceYear: 2023,
    description: "Neighbourhood spaza shop, orders stock twice a week.",
    photoUrl: "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=200&h=200&fit=crop",
  },
  {
    id: "biz_002",
    businessName: "Thabo's Corner Store",
    category: "Retail",
    location: "Tzaneen",
    memberSinceYear: 2024,
    description: "",
    photoUrl: null,
  },
];

const connectionState = new Map<string, ConnectionStatus>();

function toSearchResult(business: MockBusiness): BusinessSearchResult {
  return {
    id: business.id,
    businessName: business.businessName,
    category: business.category,
    location: business.location,
    photoUrl: business.photoUrl,
  };
}

export async function searchBusinesses(query: string): Promise<BusinessSearchResult[]> {
  await latency();

  const trimmed = query.trim();
  if (trimmed.length < 2) return [];

  // PREFIX match only, matching BusinessProfileRepository.
  // search_by_name_prefix exactly — never a substring scan (file.txt §4).
  const lower = trimmed.toLowerCase();
  return MOCK_BUSINESSES.filter((b) => b.businessName.toLowerCase().startsWith(lower)).map(toSearchResult);
}

export async function getBusinessProfile(id: string): Promise<BusinessProfilePreview | null> {
  await latency(300);
  const business = MOCK_BUSINESSES.find((b) => b.id === id);
  if (!business) return null;
  recordRecentlyViewed({ id: business.id, businessName: business.businessName });
  return {
    id: business.id,
    businessName: business.businessName,
    category: business.category,
    location: business.location,
    memberSinceYear: business.memberSinceYear,
    description: business.description || null,
    connectionStatus: connectionState.get(id) ?? "NOT_REQUESTED",
    photoUrl: business.photoUrl,
  };
}

export async function requestConnection(businessId: string): Promise<ConnectionStatus> {
  await latency(400);
  const current = connectionState.get(businessId) ?? "NOT_REQUESTED";
  if (current === "PENDING" || current === "ACTIVE") {
    return current;
  }
  connectionState.set(businessId, "PENDING");
  return "PENDING";
}

export async function inviteBusiness(_email: string): Promise<{ status: "SENT" }> {
  await latency(400);
  return { status: "SENT" };
}
