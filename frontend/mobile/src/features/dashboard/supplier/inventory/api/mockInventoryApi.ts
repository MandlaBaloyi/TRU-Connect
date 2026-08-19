/**
 * Inventory — mock implementation. Composes Products (fetched fresh
 * via products/api/productsApi.ts on every read -- never a cached
 * copy) with this file's own local inventory records. This file is
 * never imported directly by a hook/screen/component -- only
 * api/inventoryApi.ts (the mock/http switch) touches it, same
 * discipline as every other feature's own mock file in this app.
 *
 * ARCHIVED PRODUCTS NEVER APPEAR HERE -- getProducts({}) already
 * excludes them (same default as the Products list's own "All"
 * filter), and an archived product has nothing left to track stock
 * for.
 *
 * LAZY INVENTORY CREATION -- a product created after this mock's own
 * seed data (via Add Product) has no inventory record yet. Rather than
 * skip it from the list (which would silently hide a real product) or
 * require a separate "set up inventory" step, a default record
 * (0 on hand, threshold 5 -- so it starts OUT_OF_STOCK, an honest
 * default, not a guess) is created the first time it's looked up. A
 * real backend would do the equivalent via a DB default/trigger
 * alongside product creation, not a lazy read-time check -- this
 * mock's shortcut doesn't change the contract callers see.
 */

import type {
  InventoryFilters,
  InventoryItem,
  InventoryListItem,
  InventorySettings,
  InventorySummary,
  SetLowStockThresholdInput,
  StockAdjustmentInput,
} from "../types";
import { InventoryError } from "../types";
import { computeAvailableQuantity, computeInventoryStatus } from "../algorithms/computeInventoryStatus";
import { getProducts } from "../../products/api/productsApi";
import type { Product } from "../../products/types";

function generateId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function nowIso(): string {
  return new Date().toISOString();
}

const latency = (ms = 350) => new Promise<void>((resolve) => setTimeout(resolve, ms));

const MOCK_SUPPLIER_ID = "mock-supplier-001";

let mockSettings: InventorySettings = {
  defaultLowStockThreshold: 5,
  lowStockAlertChannel: "IN_APP",
};

// Seeded against the exact product ids products/api/mockProductsApi.ts
// itself seeds (prod_0001..prod_0004) -- prod_0005 is deliberately
// absent, since it's seeded archived there and archived products never
// appear in Inventory.
let mockInventory: InventoryItem[] = [
  {
    id: "inv_0001",
    productId: "prod_0001",
    supplierId: MOCK_SUPPLIER_ID,
    quantityOnHand: 47,
    quantityReserved: 0,
    lowStockThreshold: 10,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
  {
    id: "inv_0002",
    productId: "prod_0002",
    supplierId: MOCK_SUPPLIER_ID,
    quantityOnHand: 8,
    quantityReserved: 0,
    lowStockThreshold: 10,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
  {
    id: "inv_0003",
    productId: "prod_0003",
    supplierId: MOCK_SUPPLIER_ID,
    quantityOnHand: 67,
    quantityReserved: 0,
    lowStockThreshold: 15,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
  {
    id: "inv_0004",
    productId: "prod_0004",
    supplierId: MOCK_SUPPLIER_ID,
    quantityOnHand: 0,
    quantityReserved: 0,
    lowStockThreshold: 5,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
];

function getOrCreateInventoryItem(productId: string): InventoryItem {
  const existing = mockInventory.find((item) => item.productId === productId);
  if (existing) return existing;

  const created: InventoryItem = {
    id: generateId("inv"),
    productId,
    supplierId: MOCK_SUPPLIER_ID,
    quantityOnHand: 0,
    quantityReserved: 0,
    lowStockThreshold: mockSettings.defaultLowStockThreshold,
    createdAt: nowIso(),
    updatedAt: nowIso(),
  };
  mockInventory = [...mockInventory, created];
  return created;
}

function toListItem(product: Product, inventory: InventoryItem): InventoryListItem {
  return {
    product: {
      id: product.id,
      name: product.name,
      category: product.category,
      priceCents: product.priceCents,
      sellingUnit: product.sellingUnit,
      images: product.images,
      isArchived: product.isArchived,
    },
    inventory,
    status: computeInventoryStatus(inventory),
    availableQuantity: computeAvailableQuantity(inventory),
  };
}

function matchesFilter(item: InventoryListItem, filters: InventoryFilters): boolean {
  if (filters.filter && filters.filter !== "ALL" && item.status !== filters.filter) return false;
  if (filters.searchTerm) {
    const q = filters.searchTerm.trim().toLowerCase();
    if (q && !item.product.name.toLowerCase().includes(q)) return false;
  }
  return true;
}

export async function getInventoryList(filters: InventoryFilters = {}): Promise<InventoryListItem[]> {
  await latency();
  const products = await getProducts({});
  const items = products.map((product) => toListItem(product, getOrCreateInventoryItem(product.id)));
  return items.filter((item) => matchesFilter(item, filters)).sort((a, b) => a.product.name.localeCompare(b.product.name));
}

export async function getInventoryItem(productId: string): Promise<InventoryListItem> {
  await latency(200);
  const products = await getProducts({});
  const product = products.find((p) => p.id === productId);
  if (!product) throw new InventoryError("Product not found.", "PRODUCT_NOT_FOUND");
  return toListItem(product, getOrCreateInventoryItem(productId));
}

export async function getInventorySummary(): Promise<InventorySummary> {
  const items = await getInventoryList({});
  return {
    totalProducts: items.length,
    inStockCount: items.filter((i) => i.status === "IN_STOCK").length,
    lowStockCount: items.filter((i) => i.status === "LOW_STOCK").length,
    outOfStockCount: items.filter((i) => i.status === "OUT_OF_STOCK").length,
  };
}

export async function adjustStock(input: StockAdjustmentInput): Promise<InventoryListItem> {
  await latency(400);
  const products = await getProducts({});
  const product = products.find((p) => p.id === input.productId);
  if (!product) throw new InventoryError("Product not found.", "PRODUCT_NOT_FOUND");

  const current = getOrCreateInventoryItem(input.productId);
  const nextOnHand = current.quantityOnHand + input.quantityDelta;
  if (nextOnHand < 0) {
    throw new InventoryError(
      `That would take stock below zero (currently ${current.quantityOnHand}).`,
      "INSUFFICIENT_STOCK"
    );
  }

  const updated: InventoryItem = { ...current, quantityOnHand: nextOnHand, updatedAt: nowIso() };
  mockInventory = mockInventory.map((item) => (item.id === updated.id ? updated : item));
  return toListItem(product, updated);
}

export async function setLowStockThreshold(input: SetLowStockThresholdInput): Promise<InventoryListItem> {
  await latency(300);
  const products = await getProducts({});
  const product = products.find((p) => p.id === input.productId);
  if (!product) throw new InventoryError("Product not found.", "PRODUCT_NOT_FOUND");
  if (input.lowStockThreshold < 0) {
    throw new InventoryError("Low-stock threshold can't be negative.", "VALIDATION_ERROR");
  }

  const current = getOrCreateInventoryItem(input.productId);
  const updated: InventoryItem = { ...current, lowStockThreshold: input.lowStockThreshold, updatedAt: nowIso() };
  mockInventory = mockInventory.map((item) => (item.id === updated.id ? updated : item));
  return toListItem(product, updated);
}

export async function getInventorySettings(): Promise<InventorySettings> {
  await latency(200);
  return mockSettings;
}

export async function updateInventorySettings(input: Partial<InventorySettings>): Promise<InventorySettings> {
  await latency(300);
  if (input.defaultLowStockThreshold !== undefined && input.defaultLowStockThreshold < 0) {
    throw new InventoryError("Default low-stock threshold can't be negative.", "VALIDATION_ERROR");
  }
  mockSettings = { ...mockSettings, ...input };
  return mockSettings;
}
