/**
 * Products — real backend implementation. NOT YET CALLABLE END-TO-END:
 * the backend's Product model is still the deliberately minimal
 * {id, name, supplier_profile_id} slice built only to back the ordering
 * gate (can_place_order) -- it doesn't have category/price/unit/
 * stock_status/images/archived yet. This file is written against the
 * CONTRACT this feature has already committed to (types.ts), so growing
 * the backend model to match is the only thing that needs to happen
 * before flipping EXPO_PUBLIC_USE_MOCK_API off for this feature -- this
 * file itself shouldn't need to change shape when that lands.
 *
 * Route paths follow the existing supplier-discovery namespace
 * (/api/v1/supplier-discovery/*) rather than inventing a new one,
 * matching this codebase's current real routing, not a doc-derived
 * guess.
 */
import { apiGet, apiPost, apiPut, ApiError } from "@/services/api/apiClient";

import type { CreateProductInput, Product, ProductFilters, StockStatus, UpdateProductInput } from "../types";
import type { PriceAdjustment } from "../../bulk-products/types";
import { ProductsError } from "../types";

interface ApiProduct {
  id: string;
  supplier_profile_id: string;
  name: string;
  category: string;
  price_cents: number;
  selling_unit: string;
  unit_quantity: number | null;
  unit_measure: string | null;
  stock_status: string;
  images: string[];
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

function fromApiProduct(dto: ApiProduct): Product {
  return {
    id: dto.id,
    supplierId: dto.supplier_profile_id,
    name: dto.name,
    category: dto.category as Product["category"],
    priceCents: dto.price_cents,
    sellingUnit: dto.selling_unit as Product["sellingUnit"],
    unitQuantity: dto.unit_quantity,
    unitMeasure: dto.unit_measure as Product["unitMeasure"],
    stockStatus: dto.stock_status as Product["stockStatus"],
    images: dto.images,
    isArchived: dto.is_archived,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

export async function getProducts(filters: ProductFilters = {}): Promise<Product[]> {
  const data = await apiGet<{ results: ApiProduct[] }>("/supplier-discovery/products", {
    params: {
      q: filters.searchTerm || undefined,
      filter: filters.listFilter,
    },
  });
  return data.results.map(fromApiProduct);
}

export async function getProduct(id: string): Promise<Product> {
  try {
    const data = await apiGet<ApiProduct>(`/supplier-discovery/products/${id}`);
    return fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
    }
    throw error;
  }
}

export async function createProduct(input: CreateProductInput): Promise<Product> {
  try {
    const data = await apiPost<ApiProduct>("/supplier-discovery/products", {
      name: input.name.trim(),
      category: input.category,
      price_cents: input.priceCents,
      selling_unit: input.sellingUnit,
      // Image upload is a separate call against the Cloudinary pipeline
      // (sub-goal 3) -- creation itself never carries local file URIs
      // to the backend, only already-hosted URLs once they exist (see
      // the follow-up PATCH this screen will need once that pipeline
      // lands). stock_status is NOT sent -- Inventory owns stock
      // status now (see products/types.ts's own Product.stockStatus
      // docstring); the real backend seeds an Inventory record
      // separately, matching AddProductScreen's own two-call sequence.
    });
    return fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "VALIDATION_ERROR") {
      // Per-field mapping isn't defined yet -- the real envelope
      // ({success, message, data, errors, code}, src/core/responses.py)
      // carries a flat errors[] list, not a field-keyed object. Revisit
      // once the real POST /supplier-discovery/products endpoint exists
      // and its actual validation-error shape is known, rather than
      // guessing a field mapping here now.
      throw new ProductsError(error.message, "VALIDATION_ERROR");
    }
    throw error;
  }
}

export async function archiveProduct(id: string): Promise<Product> {
  try {
    const data = await apiPost<ApiProduct>(`/supplier-discovery/products/${id}/archive`, {});
    return fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
    }
    throw error;
  }
}

export async function updateProduct(input: UpdateProductInput): Promise<Product> {
  try {
    const data = await apiPut<ApiProduct>(`/supplier-discovery/products/${input.id}`, {
      name: input.name.trim(),
      category: input.category,
      price_cents: input.priceCents,
      selling_unit: input.sellingUnit,
      // stock_status intentionally not sent -- Edit Product no longer
      // touches it, same reasoning as createProduct above.
      // Same caveat as createProduct: image upload is a separate call
      // against the Cloudinary pipeline (sub-goal 3). This won't carry
      // the mixed local/remote `images` array until that's real.
    });
    return fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "VALIDATION_ERROR") {
      throw new ProductsError(error.message, "VALIDATION_ERROR");
    }
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
    }
    throw error;
  }
}

// ---------------------------------------------------------------------------
// Bulk actions -- each is ONE request carrying every selected id, not N
// sequential requests. This matters beyond just being tidy: N requests
// for a 200-product selection is 200 round trips, 200 chances to
// partially fail, and no way to report "197 succeeded, 3 didn't" as a
// single coherent result -- exactly the kind of thing this feature's
// own bulk-import security/architecture discussion was about avoiding.
// The real backend endpoints below don't exist yet (same "not callable
// end-to-end" caveat as the rest of this file); shaped this way now so
// wiring them later doesn't change this file's callers.
// ---------------------------------------------------------------------------

export async function bulkUpdateStockStatus(productIds: string[], stockStatus: StockStatus): Promise<Product[]> {
  const data = await apiPost<{ results: ApiProduct[] }>("/supplier-discovery/products/bulk/stock-status", {
    product_ids: productIds,
    stock_status: stockStatus,
  });
  return data.results.map(fromApiProduct);
}

export async function bulkAdjustPrice(productIds: string[], adjustment: PriceAdjustment): Promise<Product[]> {
  const data = await apiPost<{ results: ApiProduct[] }>("/supplier-discovery/products/bulk/adjust-price", {
    product_ids: productIds,
    direction: adjustment.direction,
    adjustment_type: adjustment.type,
    value: adjustment.value,
  });
  return data.results.map(fromApiProduct);
}

export async function bulkArchiveProducts(productIds: string[]): Promise<Product[]> {
  const data = await apiPost<{ results: ApiProduct[] }>("/supplier-discovery/products/bulk/archive", {
    product_ids: productIds,
  });
  return data.results.map(fromApiProduct);
}
