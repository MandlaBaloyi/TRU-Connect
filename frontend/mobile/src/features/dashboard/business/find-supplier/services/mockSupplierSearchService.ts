/**
 * Supplier search service — THE SINGLE INTEGRATION BOUNDARY for Find
 * Supplier, MOCK implementation. Same discipline as
 * my-account/services/accountService.ts: every function below is
 * mock-backed. Selected by services/supplierSearchService.ts (the
 * actual boundary hooks/screens import) based on
 * EXPO_PUBLIC_USE_MOCK_API — same mock/http split pattern as
 * business-profile/api/businessProfileApi.ts, now that the real
 * backend exists and httpSupplierSearchService.ts is the other half.
 *
 * SEARCH IS NAME/BUSINESS-NAME PREFIX MATCH ONLY, mirroring the real
 * backend exactly (SupplierProfileRepository.search_by_name_prefix) —
 * phone/email exact-match search was removed (see types.ts's own file
 * header for the full reasoning), and this mock's matching logic was
 * also changed from a substring `.includes()` scan to a genuine
 * prefix match, since a substring scan was never what the real
 * backend does (file.txt §4: "should NOT expose everybody" — a
 * prefix-only rule is part of that privacy narrowing, not just a
 * performance detail) and this mock exists specifically to exercise
 * the UI against the real shape/behaviour, not a more permissive one.
 */
import type {
  ConnectionStatus,
  SupplierProduct,
  SupplierProfilePreview,
  SupplierSearchResult,
  SupplierVerificationStatus,
} from "../types";
import { recordRecentlyViewed } from "./recentSearchesStore";

const latency = (ms = 500) => new Promise<void>((resolve) => setTimeout(resolve, ms));

interface MockSupplier {
  id: string;
  businessName: string;
  category: string;
  location: string;
  verificationStatus: SupplierVerificationStatus;
  memberSinceYear: number;
  description: string;
  /** null for most mock suppliers on purpose — mirrors the real
   *  default (visible_image_source=NONE) so the UI's no-photo
   *  fallback state gets exercised too, not just the happy path. */
  photoUrl: string | null;
  productCount: number;
}

// Mock "database" — deliberately includes messy real-world input
// (spacing, casing) so name-prefix matching has something real to
// prove itself against.
const MOCK_SUPPLIERS: MockSupplier[] = [
  {
    id: "sup_001",
    businessName: "ABC Wholesale",
    category: "Wholesale beverages",
    location: "Polokwane",
    verificationStatus: "verified",
    memberSinceYear: 2023,
    description: "Bulk soft drinks, water, and snacks for spaza shops and small retailers.",
    photoUrl: "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=200&h=200&fit=crop",
    productCount: 3,
  },
  {
    id: "sup_002",
    businessName: "Mabena Fresh Produce",
    category: "Fresh produce",
    location: "Polokwane",
    verificationStatus: "pending",
    memberSinceYear: 2024,
    description: "Fruit and vegetables, delivered twice a week.",
    photoUrl: null,
    productCount: 0,
  },
  {
    id: "sup_003",
    businessName: "Sekhu Bakery Supplies",
    category: "Bakery ingredients",
    location: "Tzaneen",
    verificationStatus: "unverified",
    memberSinceYear: 2025,
    description: "",
    photoUrl: null,
    productCount: 0,
  },
];

// In-memory connection-request state, module-scope, session-persistent
// — same mock discipline as accountService.ts (resets on app restart,
// never touches AsyncStorage/secureStorage, since this is genuinely
// backend-authoritative data once the real relationship domain exists).
const connectionState = new Map<string, ConnectionStatus>();

function toSearchResult(supplier: MockSupplier): SupplierSearchResult {
  return {
    id: supplier.id,
    businessName: supplier.businessName,
    category: supplier.category,
    location: supplier.location,
    verificationStatus: supplier.verificationStatus,
    photoUrl: supplier.photoUrl,
  };
}

export async function searchSuppliers(query: string): Promise<SupplierSearchResult[]> {
  await latency();

  const trimmed = query.trim();
  if (trimmed.length < 2) return [];

  // PREFIX match only, matching SupplierProfileRepository.
  // search_by_name_prefix exactly — never a substring scan anywhere
  // in the middle of a name (file.txt §4).
  const lower = trimmed.toLowerCase();
  return MOCK_SUPPLIERS.filter((s) => s.businessName.toLowerCase().startsWith(lower)).map(toSearchResult);
}

export async function getSupplierProfile(id: string): Promise<SupplierProfilePreview | null> {
  await latency(300);
  const supplier = MOCK_SUPPLIERS.find((s) => s.id === id);
  if (!supplier) return null;
  recordRecentlyViewed({ id: supplier.id, businessName: supplier.businessName });
  return {
    id: supplier.id,
    businessName: supplier.businessName,
    category: supplier.category,
    location: supplier.location,
    verificationStatus: supplier.verificationStatus,
    memberSinceYear: supplier.memberSinceYear,
    description: supplier.description || null,
    connectionStatus: connectionState.get(id) ?? "NOT_REQUESTED",
    photoUrl: supplier.photoUrl,
    productCount: supplier.productCount,
  };
}

export async function requestConnection(supplierId: string): Promise<ConnectionStatus> {
  await latency(400);
  const current = connectionState.get(supplierId) ?? "NOT_REQUESTED";
  if (current === "PENDING" || current === "ACTIVE") {
    return current; // idempotent — tapping twice doesn't double-request
  }
  connectionState.set(supplierId, "PENDING");
  return "PENDING";
}

export async function inviteSupplier(_email: string): Promise<{ status: "SENT" }> {
  await latency(400);
  return { status: "SENT" };
}

// Keyed by supplier id, matching each MOCK_SUPPLIERS entry's own
// productCount above — sup_001 has real entries, the other two stay
// empty, so the honest "nothing listed yet" state gets exercised too.
const MOCK_PRODUCTS: Record<string, SupplierProduct[]> = {
  sup_001: [
    { id: "prod_001", name: "Coca-Cola 330ml (24-pack)" },
    { id: "prod_002", name: "Bottled water 500ml (24-pack)" },
    { id: "prod_003", name: "Assorted chips (30-pack)" },
  ],
  sup_002: [],
  sup_003: [],
};

export async function getSupplierProducts(supplierId: string): Promise<SupplierProduct[]> {
  await latency(300);
  return MOCK_PRODUCTS[supplierId] ?? [];
}
