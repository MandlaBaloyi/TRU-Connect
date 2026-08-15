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
 * The mock data below deliberately exercises the real privacy
 * narrowing (masked identifiers, no full contact details) so the UI
 * was built against the actual shape it receives from the real
 * backend too, not a convenient shortcut that needed rework later.
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
  phone: string; // unmasked in the mock "database" only — never returned as-is
  email: string; // unmasked in the mock "database" only — never returned as-is
  /** null for most mock suppliers on purpose — mirrors the real
   *  default (visible_image_source=NONE) so the UI's no-photo
   *  fallback state gets exercised too, not just the happy path. */
  photoUrl: string | null;
  productCount: number;
}

// Mock "database" — deliberately includes messy real-world input
// (spacing, casing) so normalization/matching has something real to
// prove itself against once the backend exists.
const MOCK_SUPPLIERS: MockSupplier[] = [
  {
    id: "sup_001",
    businessName: "ABC Wholesale",
    category: "Wholesale beverages",
    location: "Polokwane",
    verificationStatus: "verified",
    memberSinceYear: 2023,
    description: "Bulk soft drinks, water, and snacks for spaza shops and small retailers.",
    phone: "+27712345678",
    email: "orders@abcwholesale.co.za",
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
    phone: "+27823456789",
    email: "mabenaproduce@email.com",
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
    phone: "+27734567890",
    email: "sekhubakery@email.com",
    photoUrl: null,
    productCount: 0,
  },
];

// In-memory connection-request state, module-scope, session-persistent
// — same mock discipline as accountService.ts (resets on app restart,
// never touches AsyncStorage/secureStorage, since this is genuinely
// backend-authoritative data once the real relationship domain exists).
const connectionState = new Map<string, ConnectionStatus>();

function maskEmail(email: string): string {
  const [local, domain] = email.split("@");
  if (!domain) return "***";
  if (local.length <= 2) return `${local[0]}*@${domain}`;
  return `${local[0]}${"*".repeat(local.length - 2)}${local[local.length - 1]}@${domain}`;
}

function maskPhone(phone: string): string {
  // +27712345678 -> +27 71 *** 45 78 — enough to recognise, not enough
  // to reconstruct the full number from a screenshot.
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
    // Crude local-mock normalization only — real E.164 normalization
    // is a backend concern (types.ts's contract note; the real
    // implementation should use a proper library, not this).
    const digits = query.replace(/\D/g, "");
    if (digits.startsWith("0")) return `+27${digits.slice(1)}`;
    if (digits.startsWith("27")) return `+${digits}`;
    return `+${digits}`;
  }
  return query.trim().toLowerCase();
}

function toSearchResult(supplier: MockSupplier, matchedField: SupplierSearchResult["matchedField"]): SupplierSearchResult {
  return {
    id: supplier.id,
    businessName: supplier.businessName,
    category: supplier.category,
    location: supplier.location,
    verificationStatus: supplier.verificationStatus,
    matchedField,
    maskedMatchedIdentifier:
      matchedField === "EMAIL" ? maskEmail(supplier.email) : matchedField === "PHONE" ? maskPhone(supplier.phone) : "",
    photoUrl: supplier.photoUrl,
  };
}

export async function searchSuppliers(query: string): Promise<SupplierSearchResult[]> {
  await latency();

  const trimmed = query.trim();
  if (trimmed.length < 2) return [];

  const normalized = normalizeForMatch(trimmed);

  if (looksLikeEmail(trimmed)) {
    const match = MOCK_SUPPLIERS.find((s) => s.email.toLowerCase() === normalized);
    return match ? [toSearchResult(match, "EMAIL")] : [];
  }

  if (looksLikePhone(trimmed)) {
    const match = MOCK_SUPPLIERS.find((s) => s.phone === normalized);
    return match ? [toSearchResult(match, "PHONE")] : [];
  }

  // Name search — exact/near-exact only, never a broad substring scan
  // across everything (file.txt §4: "should NOT expose everybody").
  const lower = trimmed.toLowerCase();
  return MOCK_SUPPLIERS.filter((s) => s.businessName.toLowerCase().includes(lower)).map((s) =>
    toSearchResult(s, "NAME")
  );
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
