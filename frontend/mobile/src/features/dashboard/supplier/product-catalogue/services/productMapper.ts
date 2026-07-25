import type {
  Product,
  CreateProductInput,
  UpdateProductInput,
} from '../types';

/**
 * Converts between the snake_case shape returned by the Flask API
 * (Document 04 §4.3 supplier_products / supplier_product_images) and the
 * camelCase shape used throughout the React Native app.
 *
 * Keeping this mapping in one place is what lets the rest of the feature
 * (hooks, components, screens) stay unchanged once the real backend is
 * connected — only api/productCatalogueApi.ts needs to flip its mock
 * switch.
 */

interface ApiBulkPricingTier {
  id: string;
  min_quantity: number;
  price: number;
}

interface ApiProductImage {
  id: string;
  product_id: string;
  image_url: string;
  sort_order: number;
}

export interface ApiProduct {
  id: string;
  supplier_id: string;
  category_id: string;
  category_name?: string;
  name: string;
  description: string;
  price: number;
  unit: string;
  bulk_pricing_rules: ApiBulkPricingTier[];
  minimum_order_quantity: number;
  stock_status: string;
  is_published: boolean;
  images: ApiProductImage[];
  created_at: string;
  updated_at: string;
}

export function fromApiProduct(api: ApiProduct): Product {
  return {
    id: api.id,
    supplierId: api.supplier_id,
    categoryId: api.category_id,
    categoryName: api.category_name ?? '',
    name: api.name,
    description: api.description,
    price: api.price,
    unit: api.unit,
    bulkPricingRules: (api.bulk_pricing_rules ?? []).map((tier) => ({
      id: tier.id,
      minQuantity: tier.min_quantity,
      price: tier.price,
    })),
    minimumOrderQuantity: api.minimum_order_quantity,
    stockStatus: api.stock_status as Product['stockStatus'],
    isPublished: api.is_published,
    images: (api.images ?? []).map((image) => ({
      id: image.id,
      productId: image.product_id,
      imageUrl: image.image_url,
      sortOrder: image.sort_order,
    })),
    createdAt: api.created_at,
    updatedAt: api.updated_at,
  };
}

export function toApiCreatePayload(input: CreateProductInput) {
  return {
    category_id: input.categoryId,
    name: input.name,
    description: input.description,
    price: input.price,
    unit: input.unit,
    bulk_pricing_rules: (input.bulkPricingRules ?? []).map((tier) => ({
      min_quantity: tier.minQuantity,
      price: tier.price,
    })),
    minimum_order_quantity: input.minimumOrderQuantity,
    stock_status: input.stockStatus,
    is_published: input.isPublished,
  };
}

export function toApiUpdatePayload(input: UpdateProductInput) {
  const payload: Record<string, unknown> = {};
  if (input.categoryId !== undefined) payload.category_id = input.categoryId;
  if (input.name !== undefined) payload.name = input.name;
  if (input.description !== undefined) payload.description = input.description;
  if (input.price !== undefined) payload.price = input.price;
  if (input.unit !== undefined) payload.unit = input.unit;
  if (input.bulkPricingRules !== undefined) {
    payload.bulk_pricing_rules = input.bulkPricingRules.map((tier) => ({
      min_quantity: tier.minQuantity,
      price: tier.price,
    }));
  }
  if (input.minimumOrderQuantity !== undefined) {
    payload.minimum_order_quantity = input.minimumOrderQuantity;
  }
  if (input.stockStatus !== undefined) payload.stock_status = input.stockStatus;
  if (input.isPublished !== undefined) payload.is_published = input.isPublished;
  return payload;
}
