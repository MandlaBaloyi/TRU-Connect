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
  UpdateProductInput,
} from "../types";
import { ProductsError } from "../types";
import type { PriceAdjustment } from "../../bulk-products/types";
import { applyPriceAdjustment } from "../../bulk-products/algorithms/priceAdjustment";
import { computeCompareAtPrice } from "../algorithms/discount";

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
    compareAtPriceCents: null,
    sellingUnit: "BOTTLE",
    unitQuantity: null,
    unitMeasure: null,
    description: null,
    sku: "SKU-0001",
    productCode: "TRU-3F7K9M",
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
    // A real example of the "was RX, now RY" comparison price -- shows
    // crossed out next to the real price on Product Detail.
    compareAtPriceCents: 2500,
    sellingUnit: "BOTTLE",
    unitQuantity: null,
    unitMeasure: null,
    description: null,
    sku: "SKU-0002",
    productCode: "TRU-7H2N4P",
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
    compareAtPriceCents: null,
    sellingUnit: "EACH",
    unitQuantity: null,
    unitMeasure: null,
    description: null,
    sku: "SKU-0003",
    productCode: "TRU-5R8T2W",
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
    compareAtPriceCents: null,
    sellingUnit: "EACH",
    unitQuantity: null,
    unitMeasure: null,
    // A real example of the description field, matching the exact
    // "3 loaves per case" style already discussed for bulk import.
    description: "Sliced white bread. 1 loaf per unit.",
    sku: "SKU-0004",
    productCode: "TRU-9K3X6L",
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
    compareAtPriceCents: null,
    sellingUnit: "BOTTLE",
    unitQuantity: null,
    unitMeasure: null,
    description: null,
    sku: "SKU-0005",
    productCode: "TRU-2M6Q8V",
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

let mockSkuCounter = mockProducts.length;

/** Mirrors the real backend's own per-supplier sequential counter in
 *  spirit (SKU-0001, SKU-0002...) -- doesn't need the real atomic-
 *  update rigor here, this is a single in-memory session, never
 *  genuinely concurrent. */
function generateMockSku(): string {
  mockSkuCounter += 1;
  return `SKU-${String(mockSkuCounter).padStart(4, "0")}`;
}

const _PRODUCT_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";

/** Mirrors the real backend's own algorithms/product_code_generator.py
 *  -- same alphabet (excludes 0/O/1/I), same collision-checked retry,
 *  just against the in-memory mock list instead of a real database. */
function generateMockProductCode(): string {
  let candidate: string;
  do {
    candidate =
      "TRU-" +
      Array.from({ length: 6 }, () => _PRODUCT_CODE_ALPHABET[Math.floor(Math.random() * _PRODUCT_CODE_ALPHABET.length)]).join("");
  } while (mockProducts.some((p) => p.productCode === candidate));
  return candidate;
}

function validate(
  input: Pick<CreateProductInput, "name" | "priceCents"> & {
    compareAtPriceCents?: number;
    sku?: string;
    supplierId?: string;
    excludeProductId?: string;
  }
): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!input.name.trim()) errors.name = "Enter a product name.";
  if (input.priceCents === null || input.priceCents === undefined || input.priceCents < 0) {
    errors.priceCents = "Enter a valid price.";
  }
  if (input.compareAtPriceCents !== undefined && input.compareAtPriceCents !== null) {
    if (input.compareAtPriceCents <= input.priceCents) {
      errors.compareAtPriceCents = "Compare-at price must be higher than the actual price to show as a discount.";
    }
  }
  if (input.sku && input.sku.trim()) {
    const collision = mockProducts.some(
      (p) => p.sku === input.sku!.trim() && p.supplierId === MOCK_SUPPLIER_ID && p.id !== input.excludeProductId
    );
    if (collision) {
      errors.sku = `SKU "${input.sku.trim()}" is already used by another product.`;
    }
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
    compareAtPriceCents: input.compareAtPriceCents ?? null,
    sellingUnit: input.sellingUnit,
    unitQuantity: null,
    unitMeasure: null,
    description: input.description?.trim() || null,
    // Left blank -- auto-filled, same as the real backend. Never
    // product_code -- that's never accepted as input anywhere, even
    // here in the mock.
    sku: input.sku?.trim() || generateMockSku(),
    productCode: generateMockProductCode(),
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

export async function unarchiveProduct(id: string): Promise<Product> {
  await latency(300);
  const index = mockProducts.findIndex((p) => p.id === id);
  if (index === -1) throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
  const unarchived: Product = { ...mockProducts[index], isArchived: false, updatedAt: nowIso() };
  mockProducts = [...mockProducts.slice(0, index), unarchived, ...mockProducts.slice(index + 1)];
  return unarchived;
}

export async function deleteProduct(id: string): Promise<void> {
  // Real removal from the mock array -- unlike archive, there's no
  // client-facing screen that ever needs to see a deleted product
  // again, matching the real backend's own behaviour: a soft-deleted
  // row never comes back from any client-facing query either.
  await latency(300);
  const index = mockProducts.findIndex((p) => p.id === id);
  if (index === -1) throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
  mockProducts = [...mockProducts.slice(0, index), ...mockProducts.slice(index + 1)];
}

export async function updateProduct(input: UpdateProductInput): Promise<Product> {
  await latency(400);
  const index = mockProducts.findIndex((p) => p.id === input.id);
  if (index === -1) throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");

  const fieldErrors = validate({ ...input, excludeProductId: input.id });
  if (Object.keys(fieldErrors).length > 0) {
    throw new ProductsError("Check the highlighted fields.", "VALIDATION_ERROR", fieldErrors);
  }

  const updated: Product = {
    ...mockProducts[index],
    name: input.name.trim(),
    category: input.category,
    priceCents: input.priceCents,
    compareAtPriceCents: input.compareAtPriceCents ?? mockProducts[index].compareAtPriceCents,
    // stockStatus deliberately NOT set here -- the spread above
    // already carries the existing value forward unchanged. Edit
    // Product no longer supplies one (see types.ts's own docstring).
    sellingUnit: input.sellingUnit,
    description: input.description !== undefined ? input.description.trim() || null : mockProducts[index].description,
    // undefined means "leave the existing SKU alone" -- matches the
    // real backend's own update_product semantics exactly. Never
    // product_code -- the spread above already carries it forward,
    // and nothing here ever overwrites it.
    sku: input.sku?.trim() || mockProducts[index].sku,
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

export async function bulkSetDiscount(productIds: string[], discountPercent: number): Promise<Product[]> {
  await latency(400);
  // Same rule as the real backend's own product_service.py::
  // bulk_set_discount -- 0 isn't a real discount, 100+ divides by
  // zero or goes negative. Checked before touching anything, matching
  // the real backend's all-or-nothing behaviour for the whole batch.
  if (discountPercent <= 0 || discountPercent >= 100) {
    throw new ProductsError("Check the highlighted fields.", "VALIDATION_ERROR", {
      discountPercent: "Discount must be between 1% and 99%.",
    });
  }

  const idSet = new Set(productIds);
  const updated: Product[] = [];
  mockProducts = mockProducts.map((product) => {
    if (!idSet.has(product.id)) return product;
    const next = {
      ...product,
      compareAtPriceCents: computeCompareAtPrice(product.priceCents, discountPercent),
      updatedAt: nowIso(),
    };
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

export async function bulkUnarchiveProducts(productIds: string[]): Promise<Product[]> {
  await latency(400);
  const idSet = new Set(productIds);
  const updated: Product[] = [];
  mockProducts = mockProducts.map((product) => {
    if (!idSet.has(product.id) || !product.isArchived) return product;
    const next = { ...product, isArchived: false, updatedAt: nowIso() };
    updated.push(next);
    return next;
  });
  return updated;
}

export async function bulkDeleteProducts(productIds: string[]): Promise<void> {
  await latency(400);
  const idSet = new Set(productIds);
  mockProducts = mockProducts.filter((product) => !idSet.has(product.id));
}
