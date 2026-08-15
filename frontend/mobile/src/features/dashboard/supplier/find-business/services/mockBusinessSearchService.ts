/**
 * Business search service — mock implementation. Mirrors
 * business/find-supplier/services/mockSupplierSearchService.ts
 * exactly, minus verificationStatus (BusinessProfile's real
 * to_search_result_dict/to_profile_preview_dict don't return one —
 * verified directly against those methods, see this feature's own
 * types.ts).
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
  phone: string;
  email: string;
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
    phone: "+27821234567",
    email: "mandla@example.com",
    photoUrl: "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=200&h=200&fit=crop",
  },
  {
    id: "biz_002",
    businessName: "Thabo's Corner Store",
    category: "Retail",
    location: "Tzaneen",
    memberSinceYear: 2024,
    description: "",
    phone: "+27837654321",
    email: "thabo@example.com",
    photoUrl: null,
  },
];

const connectionState = new Map<string, ConnectionStatus>();

function maskEmail(email: string): string {
  const [local, domain] = email.split("@");
  if (!domain) return "***";
  if (local.length <= 2) return `${local[0]}*@${domain}`;
  return `${local[0]}${"*".repeat(local.length - 2)}${local[local.length - 1]}@${domain}`;
}

function maskPhone(phone: string): string {
  const digits = phone.replace(/\D/g, "");
  if (digits.length < 6) return "***";
  const last4 = digits.slice(-4);
  return `${phone.slice(0, 3)} ${digits.slice(2, 4)} *** ${last4.slice(0, 2)} ${last4.slice(2)}`;
}

function looksLikeEmail(query: string): boolean {
  return query.includes("@");
}

function looksLikePhone(query: string): boolean {
  const digits = query.replace(/[\s()-]/g, "");
  return /^\+?\d{7,15}$/.test(digits);
}

function normalizeForMatch(query: string): string {
  if (looksLikeEmail(query)) return query.trim().toLowerCase();
  if (looksLikePhone(query)) {
    const digits = query.replace(/\D/g, "");
    if (digits.startsWith("0")) return `+27${digits.slice(1)}`;
    if (digits.startsWith("27")) return `+${digits}`;
    return `+${digits}`;
  }
  return query.trim().toLowerCase();
}

function toSearchResult(business: MockBusiness, matchedField: BusinessSearchResult["matchedField"]): BusinessSearchResult {
  return {
    id: business.id,
    businessName: business.businessName,
    category: business.category,
    location: business.location,
    matchedField,
    maskedMatchedIdentifier:
      matchedField === "EMAIL" ? maskEmail(business.email) : matchedField === "PHONE" ? maskPhone(business.phone) : "",
    photoUrl: business.photoUrl,
  };
}

export async function searchBusinesses(query: string): Promise<BusinessSearchResult[]> {
  await latency();

  const trimmed = query.trim();
  if (trimmed.length < 2) return [];

  const normalized = normalizeForMatch(trimmed);

  if (looksLikeEmail(trimmed)) {
    const match = MOCK_BUSINESSES.find((b) => b.email.toLowerCase() === normalized);
    return match ? [toSearchResult(match, "EMAIL")] : [];
  }

  if (looksLikePhone(trimmed)) {
    const match = MOCK_BUSINESSES.find((b) => b.phone === normalized);
    return match ? [toSearchResult(match, "PHONE")] : [];
  }

  const lower = trimmed.toLowerCase();
  return MOCK_BUSINESSES.filter((b) => b.businessName.toLowerCase().includes(lower)).map((b) =>
    toSearchResult(b, "NAME")
  );
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
