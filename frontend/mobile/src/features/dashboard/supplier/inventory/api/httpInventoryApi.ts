/**
 * Inventory — real backend implementation. NOT YET CALLABLE
 * END-TO-END: there is no backend inventory table/routes yet, same
 * "not callable" caveat as every other feature's own http api file in
 * this app. Written against the CONTRACT this feature has already
 * committed to (types.ts), so building the real backend is the only
 * thing that needs to happen before flipping EXPO_PUBLIC_USE_MOCK_API
 * off for this feature.
 *
 * Route paths follow the existing supplier-discovery namespace,
 * matching products' own precedent rather than inventing a new one.
 */

import { apiGet, apiPost, apiPut, ApiError } from "@/services/api/apiClient";

import type {
  InventoryFilters,
  InventoryListItem,
  InventorySettings,
  InventorySummary,
  SetLowStockThresholdInput,
  StockAdjustmentInput,
} from "../types";
import { InventoryError } from "../types";

interface ApiInventoryListItem {
  product: {
    id: string;
    name: string;
    category: string;
    price_cents: number;
    selling_unit: string;
    images: string[];
    is_archived: boolean;
  };
  inventory: {
    id: string;
    product_id: string;
    supplier_id: string;
    quantity_on_hand: number;
    quantity_reserved: number;
    low_stock_threshold: number;
    created_at: string;
    updated_at: string;
  };
  status: string;
  available_quantity: number;
}

function fromApiListItem(dto: ApiInventoryListItem): InventoryListItem {
  return {
    product: {
      id: dto.product.id,
      name: dto.product.name,
      category: dto.product.category as InventoryListItem["product"]["category"],
      priceCents: dto.product.price_cents,
      sellingUnit: dto.product.selling_unit as InventoryListItem["product"]["sellingUnit"],
      images: dto.product.images,
      isArchived: dto.product.is_archived,
    },
    inventory: {
      id: dto.inventory.id,
      productId: dto.inventory.product_id,
      supplierId: dto.inventory.supplier_id,
      quantityOnHand: dto.inventory.quantity_on_hand,
      quantityReserved: dto.inventory.quantity_reserved,
      lowStockThreshold: dto.inventory.low_stock_threshold,
      createdAt: dto.inventory.created_at,
      updatedAt: dto.inventory.updated_at,
    },
    status: dto.status as InventoryListItem["status"],
    availableQuantity: dto.available_quantity,
  };
}

export async function getInventoryList(filters: InventoryFilters = {}): Promise<InventoryListItem[]> {
  const data = await apiGet<{ results: ApiInventoryListItem[] }>("/supplier-discovery/inventory", {
    params: { q: filters.searchTerm || undefined, filter: filters.filter },
  });
  return data.results.map(fromApiListItem);
}

export async function getInventoryItem(productId: string): Promise<InventoryListItem> {
  try {
    const data = await apiGet<ApiInventoryListItem>(`/supplier-discovery/inventory/${productId}`);
    return fromApiListItem(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      throw new InventoryError("Product not found.", "PRODUCT_NOT_FOUND");
    }
    throw error;
  }
}

export async function getInventorySummary(): Promise<InventorySummary> {
  const data = await apiGet<{
    total_products: number;
    in_stock_count: number;
    low_stock_count: number;
    out_of_stock_count: number;
  }>("/supplier-discovery/inventory/summary");
  return {
    totalProducts: data.total_products,
    inStockCount: data.in_stock_count,
    lowStockCount: data.low_stock_count,
    outOfStockCount: data.out_of_stock_count,
  };
}

export async function adjustStock(input: StockAdjustmentInput): Promise<InventoryListItem> {
  try {
    const data = await apiPost<ApiInventoryListItem>(`/supplier-discovery/inventory/${input.productId}/adjust`, {
      quantity_delta: input.quantityDelta,
      reason: input.reason,
    });
    return fromApiListItem(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "INSUFFICIENT_STOCK") {
      throw new InventoryError(error.message, "INSUFFICIENT_STOCK");
    }
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      throw new InventoryError("Product not found.", "PRODUCT_NOT_FOUND");
    }
    throw error;
  }
}

export async function setLowStockThreshold(input: SetLowStockThresholdInput): Promise<InventoryListItem> {
  try {
    const data = await apiPut<ApiInventoryListItem>(`/supplier-discovery/inventory/${input.productId}/threshold`, {
      low_stock_threshold: input.lowStockThreshold,
    });
    return fromApiListItem(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "VALIDATION_ERROR") {
      throw new InventoryError(error.message, "VALIDATION_ERROR");
    }
    throw error;
  }
}

export async function getInventorySettings(): Promise<InventorySettings> {
  const data = await apiGet<{ default_low_stock_threshold: number; low_stock_alert_channel: string }>(
    "/supplier-discovery/inventory/settings"
  );
  return {
    defaultLowStockThreshold: data.default_low_stock_threshold,
    lowStockAlertChannel: data.low_stock_alert_channel as InventorySettings["lowStockAlertChannel"],
  };
}

export async function updateInventorySettings(input: Partial<InventorySettings>): Promise<InventorySettings> {
  try {
    const data = await apiPut<{ default_low_stock_threshold: number; low_stock_alert_channel: string }>(
      "/supplier-discovery/inventory/settings",
      {
        default_low_stock_threshold: input.defaultLowStockThreshold,
        low_stock_alert_channel: input.lowStockAlertChannel,
      }
    );
    return {
      defaultLowStockThreshold: data.default_low_stock_threshold,
      lowStockAlertChannel: data.low_stock_alert_channel as InventorySettings["lowStockAlertChannel"],
    };
  } catch (error) {
    if (error instanceof ApiError && error.code === "VALIDATION_ERROR") {
      throw new InventoryError(error.message, "VALIDATION_ERROR");
    }
    throw error;
  }
}
