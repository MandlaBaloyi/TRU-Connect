/**
 * Products — mock implementation. Real contract shape (types.ts),
 * mock-backed data, same discipline as order-book/api/mockOrderBookApi.ts:
 * this file is never imported directly by a hook/screen/component --
 * only api/productsApi.ts (the mock/http switch) touches it.
 *
 * v2: seed data now carries multiple images (first = cover), a real
 * sellingUnit, and isArchived -- matches types.ts's own v2 shape.
 * archiveProduct() added; products are NEVER deleted from this mock,
 * matching the ACTIVE/INACTIVE/ARCHIVED discipline this whole feature
 * is built around (see ProductDetailScreen's own docstring).
 */
import type {
  CreateProductInput,
  Product,
  ProductFilters,
  ProductListFilter,
  StockStatus,
  UpdateProductInput,
} from "../types";
import { ProductsError } from "../types";
import type { PriceAdjustment } from "../../bulk-products/types";
import { applyPriceAdjustment } from "../../bulk-products/algorithms/priceAdjustment";

const MOCK_SUPPLIER_ID = "mock-supplier-001";

function generateId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function nowIso(): string {
  return new Date().toISOString();
}

const latency = (ms = 350) => new Promise<void>((resolve) => setTimeout(resolve, ms));

let mockProducts: Product[] = [
  {
    id: "prod_0001",
    supplierId: MOCK_SUPPLIER_ID,
    name: "Coca-Cola 500ml",
    category: "BEVERAGES",
    priceCents: 1200,
    sellingUnit: "BOTTLE",
    unitQuantity: null,
    unitMeasure: null,
    stockStatus: "IN_STOCK",
    images: [
      "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=300&h=300&fit=crop",
      "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=300&h=300&fit=crop",
    ],
    isArchived: false,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
  {
    id: "prod_0002",
    supplierId: MOCK_SUPPLIER_ID,
    name: "Coca-Cola 1.25L",
    category: "BEVERAGES",
    priceCents: 2100,
    sellingUnit: "BOTTLE",
    unitQuantity: null,
    unitMeasure: null,
    stockStatus: "IN_STOCK",
    images: [],
    isArchived: false,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
  {
    id: "prod_0003",
    supplierId: MOCK_SUPPLIER_ID,
    name: "Simba Chips 120g",
    category: "SNACKS_CONFECTIONERY",
    priceCents: 1850,
    sellingUnit: "EACH",
    unitQuantity: null,
    unitMeasure: null,
    stockStatus: "IN_STOCK",
    images: ["https://images.unsplash.com/photo-1621447504864-d8686e12698c?w=300&h=300&fit=crop"],
    isArchived: false,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
  {
    id: "prod_0004",
    supplierId: MOCK_SUPPLIER_ID,
    name: "Albany Bread",
    category: "BAKERY",
    priceCents: 1999,
    sellingUnit: "EACH",
    unitQuantity: null,
    unitMeasure: null,
    stockStatus: "OUT_OF_STOCK",
    images: [],
    isArchived: false,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
  {
    id: "prod_0005",
    supplierId: MOCK_SUPPLIER_ID,
    name: "Fanta Orange 2L (discontinued line)",
    category: "BEVERAGES",
    priceCents: 2500,
    sellingUnit: "BOTTLE",
    unitQuantity: null,
    unitMeasure: null,
    stockStatus: "OUT_OF_STOCK",
    images: [],
    // Seeded already-archived so the Archived filter has something
    // real to show without needing to archive one manually first.
    isArchived: true,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
];

function matchesFilter(product: Product, listFilter: ProductListFilter | undefined): boolean {
  switch (listFilter) {
    case "ARCHIVED":
      return product.isArchived;
    case "IN_STOCK":
      return !product.isArchived && product.stockStatus === "IN_STOCK";
    case "OUT_OF_STOCK":
      return !product.isArchived && product.stockStatus === "OUT_OF_STOCK";
    case "ALL":
    case undefined:
    default:
      // "All" still excludes archived -- archived products are for
      // recovery/management, not everyday browsing (per review).
      return !product.isArchived;
  }
}

function applyFilters(products: Product[], filters: ProductFilters): Product[] {
  return products.filter((product) => {
    if (!matchesFilter(product, filters.listFilter)) return false;
    if (filters.searchTerm) {
      const q = filters.searchTerm.trim().toLowerCase();
      if (q && !product.name.toLowerCase().includes(q)) return false;
    }
    return true;
  });
}

export async function getProducts(filters: ProductFilters = {}): Promise<Product[]> {
  await latency();
  return applyFilters(mockProducts, filters).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

export async function getProduct(id: string): Promise<Product> {
  await latency(200);
  const found = mockProducts.find((p) => p.id === id);
  if (!found) throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
  return found;
}

function validate(input: Pick<CreateProductInput, "name" | "priceCents">): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!input.name.trim()) errors.name = "Enter a product name.";
  if (input.priceCents === null || input.priceCents === undefined || input.priceCents < 0) {
    errors.priceCents = "Enter a valid price.";
  }
  return errors;
}

export async function createProduct(input: CreateProductInput): Promise<Product> {
  await latency(400);
  const fieldErrors = validate(input);
  if (Object.keys(fieldErrors).length > 0) {
    throw new ProductsError("Check the highlighted fields.", "VALIDATION_ERROR", fieldErrors);
  }

  const product: Product = {
    id: generateId("prod"),
    supplierId: MOCK_SUPPLIER_ID,
    name: input.name.trim(),
    category: input.category,
    priceCents: input.priceCents,
    sellingUnit: input.sellingUnit,
    unitQuantity: null,
    unitMeasure: null,
    // Legacy field, no longer supplied by the form -- see this field's
    // own docstring in types.ts. Defaulted, never read by current UI.
    stockStatus: "IN_STOCK",
    // Local-only preview for now -- becomes real secure_urls once the
    // Cloudinary pipeline (sub-goal 3) uploads them. Good enough within
    // one session for reviewing the create flow.
    images: input.localImageUris,
    isArchived: false,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  };
  mockProducts = [product, ...mockProducts];
  return product;
}

export async function archiveProduct(id: string): Promise<Product> {
  await latency(300);
  const index = mockProducts.findIndex((p) => p.id === id);
  if (index === -1) throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
  const archived: Product = { ...mockProducts[index], isArchived: true, updatedAt: nowIso() };
  mockProducts = [...mockProducts.slice(0, index), archived, ...mockProducts.slice(index + 1)];
  return archived;
}

export async function updateProduct(input: UpdateProductInput): Promise<Product> {
  await latency(400);
  const index = mockProducts.findIndex((p) => p.id === input.id);
  if (index === -1) throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");

  const fieldErrors = validate(input);
  if (Object.keys(fieldErrors).length > 0) {
    throw new ProductsError("Check the highlighted fields.", "VALIDATION_ERROR", fieldErrors);
  }

  const updated: Product = {
    ...mockProducts[index],
    name: input.name.trim(),
    category: input.category,
    priceCents: input.priceCents,
    sellingUnit: input.sellingUnit,
    // stockStatus deliberately NOT set here -- the spread above
    // already carries the existing value forward unchanged. Edit
    // Product no longer supplies one (see types.ts's own docstring).
    images: input.images,
    updatedAt: nowIso(),
  };
  mockProducts = [...mockProducts.slice(0, index), updated, ...mockProducts.slice(index + 1)];
  return updated;
}

// ---------------------------------------------------------------------------
// Bulk actions -- selection-mode multi-select on the list screen. Every
// bulk function is a thin loop over the existing single-item mutation
// logic, not a separate code path -- keeps bulk and single-item
// behaviour (validation, archived-state rules) from silently drifting
// apart. Real backend implementation should batch these as one
// transaction/query, not N sequential requests -- see this feature's
// own memory of the bulk-import security/architecture discussion for
// why N-requests-per-bulk-action doesn't scale.
// ---------------------------------------------------------------------------

export async function bulkUpdateStockStatus(productIds: string[], stockStatus: StockStatus): Promise<Product[]> {
  await latency(400);
  const idSet = new Set(productIds);
  const updated: Product[] = [];
  mockProducts = mockProducts.map((product) => {
    if (!idSet.has(product.id)) return product;
    const next = { ...product, stockStatus, updatedAt: nowIso() };
    updated.push(next);
    return next;
  });
  return updated;
}

export async function bulkAdjustPrice(productIds: string[], adjustment: PriceAdjustment): Promise<Product[]> {
  await latency(400);
  const idSet = new Set(productIds);
  const updated: Product[] = [];
  mockProducts = mockProducts.map((product) => {
    if (!idSet.has(product.id)) return product;
    const next = { ...product, priceCents: applyPriceAdjustment(product.priceCents, adjustment), updatedAt: nowIso() };
    updated.push(next);
    return next;
  });
  return updated;
}

export async function bulkArchiveProducts(productIds: string[]): Promise<Product[]> {
  await latency(400);
  const idSet = new Set(productIds);
  const updated: Product[] = [];
  mockProducts = mockProducts.map((product) => {
    if (!idSet.has(product.id) || product.isArchived) return product;
    const next = { ...product, isArchived: true, updatedAt: nowIso() };
    updated.push(next);
    return next;
  });
  return updated;
}
