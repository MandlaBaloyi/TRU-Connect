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
  DisconnectReason,
  ReportReason,
  SupplierProduct,
  SupplierProductDetail,
  SupplierProductsCatalog,
  SupplierProductsQuery,
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

export async function endConnection(
  supplierId: string,
  _reason: DisconnectReason,
  _details: string | null
): Promise<void> {
  await latency(400);
  // Mirrors the real backend: the SAME connection state transitions
  // away from ACTIVE -- a subsequent getMyConnections() call in mock
  // mode correctly stops showing this supplier, matching the real
  // "vanishes from My Connections" behaviour. TERMINATED, not a
  // made-up "DISCONNECTED" string -- ConnectionStatus's own real type
  // already has this exact value for precisely this case.
  connectionState.set(supplierId, "TERMINATED");
}

export async function reportSupplier(
  _supplierId: string,
  _reason: ReportReason,
  _details: string | null,
  _productId?: string
): Promise<void> {
  await latency(400);
  // Nothing to persist in mock mode -- the real backend's own
  // "genuine, permanent record" guarantee only matters against a real
  // database, which mock mode doesn't have.
}

export async function inviteSupplier(_email: string): Promise<{ status: "SENT" }> {
  await latency(400);
  return { status: "SENT" };
}

// Keyed by supplier id, matching each MOCK_SUPPLIERS entry's own
// productCount above — sup_001 has real entries, the other two stay
// empty, so the honest "nothing listed yet" state gets exercised too.
// One entry (Assorted chips) carries a real compareAtPriceCents, so
// the "X% OFF" badge gets exercised in mock mode too, not just the
// plain-price path.
const MOCK_PRODUCTS: Record<string, SupplierProduct[]> = {
  sup_001: [
    {
      id: "prod_001",
      name: "Coca-Cola 330ml (24-pack)",
      category: "BEVERAGES",
      priceCents: 21000,
      compareAtPriceCents: null,
      sellingUnit: "CASE",
      inStock: true,
      images: ["https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400&h=400&fit=crop"],
    },
    {
      id: "prod_002",
      name: "Bottled water 500ml (24-pack)",
      category: "BEVERAGES",
      priceCents: 9500,
      compareAtPriceCents: null,
      sellingUnit: "CASE",
      inStock: false,
      images: [],
    },
    {
      id: "prod_003",
      name: "Assorted chips (30-pack)",
      category: "SNACKS_CONFECTIONERY",
      priceCents: 18500,
      compareAtPriceCents: 24000,
      sellingUnit: "CASE",
      inStock: true,
      images: ["https://images.unsplash.com/photo-1621447504864-d8686e12698c?w=400&h=400&fit=crop"],
    },
    // Programmatically generated -- 3 hand-written items above aren't
    // enough to genuinely exercise a real pager in mock mode (the
    // whole point of pagination is a supplier with MANY products).
    // 22 more, bringing sup_001 to 25 total -- enough for 2 real pages
    // at the same default limit (20) the real backend uses.
    ...Array.from({ length: 22 }, (_, i) => ({
      id: `prod_gen_${i}`,
      name: `Bulk Item ${i + 1}`,
      category: (["BEVERAGES", "SNACKS_CONFECTIONERY", "PERSONAL_CARE", "OTHER"] as const)[i % 4],
      priceCents: 1500 + i * 250,
      compareAtPriceCents: i % 5 === 0 ? 1500 + i * 250 + 500 : null,
      sellingUnit: "EACH" as const,
      // Every 6th generated item is out of stock -- enough of a mix to
      // genuinely exercise both states across a real page, not every
      // single item looking identical.
      inStock: i % 6 !== 0,
      images: [] as string[],
    })),
  ],
  sup_002: [],
  sup_003: [],
};

const MOCK_PRODUCT_DESCRIPTIONS: Record<string, string | null> = {
  prod_001: "Full case, 330ml cans. Ideal for spaza shops selling single cans.",
  prod_002: null,
  prod_003: "Mixed flavours, 30 individual packets per case.",
};

export async function getSupplierProductCategories(supplierId: string): Promise<string[]> {
  await latency(200);
  const all = MOCK_PRODUCTS[supplierId] ?? [];
  return Array.from(new Set(all.map((p) => p.category)));
}

export async function getSupplierProducts(
  supplierId: string,
  query: SupplierProductsQuery = {}
): Promise<SupplierProductsCatalog> {
  await latency(300);
  const supplier = MOCK_SUPPLIERS.find((s) => s.id === supplierId);
  const all = MOCK_PRODUCTS[supplierId] ?? [];

  // Genuinely applies sort/filter/pagination in mock mode too --
  // matching the real backend's own behaviour, not a mock that always
  // just returns everything regardless of what was asked for. Small,
  // local logic here rather than a shared helper -- my-suppliers/
  // depends on find-supplier for its own types (not the other
  // direction), so this file can't reach into that folder without
  // creating the same backward dependency already caught and fixed
  // twice elsewhere in this feature.
  const category = query.category ?? null;
  const filtered = category ? all.filter((p) => p.category === category) : all;

  const sort = query.sort ?? "NEWEST";
  const sorted = [...filtered];
  if (sort === "NAME_ASC") sorted.sort((a, b) => a.name.localeCompare(b.name));
  else if (sort === "PRICE_ASC") sorted.sort((a, b) => a.priceCents - b.priceCents);
  else if (sort === "PRICE_DESC") sorted.sort((a, b) => b.priceCents - a.priceCents);
  // "NEWEST" (default): mock array's own insertion order, no sort.

  const limit = Math.min(query.limit ?? 20, 50);
  const page = Math.max(query.page ?? 1, 1);
  const totalCount = sorted.length;
  const totalPages = Math.max(1, Math.ceil(totalCount / limit));
  const start = (page - 1) * limit;
  const pageItems = sorted.slice(start, start + limit);

  return {
    supplierName: supplier?.businessName ?? "Unknown supplier",
    // Same gate as getSupplierProduct's own mock below -- connected
    // AND sup_001 (the one mock supplier seeded with real contact
    // details).
    contact:
      connectionState.get(supplierId) === "ACTIVE" && supplierId === "sup_001"
        ? { whatsappNumber: "27821234567", email: "orders@abcwholesale.co.za", tiktokHandle: "abcwholesale" }
        : null,
    page,
    totalPages,
    totalCount,
    products: pageItems,
  };
}

export async function getSupplierProduct(
  supplierId: string,
  productId: string
): Promise<SupplierProductDetail | null> {
  await latency(300);
  const supplier = MOCK_SUPPLIERS.find((s) => s.id === supplierId);
  const product = (MOCK_PRODUCTS[supplierId] ?? []).find((p) => p.id === productId);
  if (!product || !supplier) return null;
  return {
    ...product,
    supplierName: supplier.businessName,
    // Mirrors the real gate exactly: connected (mock connection
    // state, same module as requestConnection below) AND the
    // supplier having "opted in" -- sup_001 is the one mock supplier
    // seeded with real contact details, so the happy path is
    // genuinely exercisable in mock mode too, not just the null case.
    contact:
      connectionState.get(supplierId) === "ACTIVE" && supplierId === "sup_001"
        ? { whatsappNumber: "27821234567", email: "orders@abcwholesale.co.za", tiktokHandle: "abcwholesale" }
        : null,
    description: MOCK_PRODUCT_DESCRIPTIONS[productId] ?? null,
    // A real-looking mock code, matching the real TRU-XXXXXX format --
    // not meant to be genuinely random here, just realistic.
    productCode: `TRU-${productId.slice(-6).toUpperCase()}`,
  };
}

/** Mirrors the real backend's own list_related_products exactly: same
 *  supplier, same category, excludes the product being viewed, capped
 *  at 5. Genuinely returns fewer (or zero) when that's all that
 *  matches, not padded to force a count. */
/** Mirrors the real backend's own list_related_products exactly:
 *  genuinely related (same category) products first, then any other
 *  product from this same supplier fills the remaining slots if fewer
 *  than 5 real matches exist -- see the real backend's own docstring
 *  on why (a supplier with real stock spread across many categories
 *  was showing nothing here far too often). Priority always goes to
 *  real relatedness; backfill only fills leftover slots, never
 *  displaces a genuine match, and never duplicates a product already
 *  in the related set. */
export async function getRelatedProducts(supplierId: string, productId: string): Promise<SupplierProduct[]> {
  await latency(250);
  const all = MOCK_PRODUCTS[supplierId] ?? [];
  const viewed = all.find((p) => p.id === productId);
  if (!viewed) return [];

  const related = all.filter((p) => p.id !== productId && p.category === viewed.category).slice(0, 5);
  const remaining = 5 - related.length;
  if (remaining <= 0) return related;

  const alreadyIncludedIds = new Set([productId, ...related.map((p) => p.id)]);
  const backfill = all.filter((p) => !alreadyIncludedIds.has(p.id)).slice(0, remaining);
  return [...related, ...backfill];
}
