/**
 * Product Catalogue — Shared Types
 *
 * Source of truth:
 *   - Document 04 (Database Design), Supplier Domain §4.3
 *     (supplier_products, supplier_product_images)
 *   - Document 05 (Backend API Specification), §5.3
 *   - Document 06 (Business Rules & Workflows), §4
 */

export type StockStatus = 'in_stock' | 'low_stock' | 'out_of_stock';

export interface BulkPricingTier {
  id: string;
  minQuantity: number;
  price: number;
}

export interface ProductImage {
  id: string;
  productId: string;
  imageUrl: string;
  sortOrder: number;
}

/**
 * Presentational shape only. Real category data is owned by the Platform
 * Domain (lookup_categories, Document 04 §4.7) and fetched via
 * GET /categories (Document 05 §5.7) once that feature exists.
 */
export interface ProductCategory {
  id: string;
  name: string;
  parentCategoryId: string | null;
}

export interface Product {
  id: string;
  supplierId: string;
  categoryId: string;
  categoryName: string;
  name: string;
  description: string;
  price: number;
  unit: string;
  bulkPricingRules: BulkPricingTier[];
  minimumOrderQuantity: number;
  stockStatus: StockStatus;
  isPublished: boolean;
  images: ProductImage[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateProductInput {
  categoryId: string;
  name: string;
  description: string;
  price: number;
  unit: string;
  bulkPricingRules?: Omit<BulkPricingTier, 'id'>[];
  minimumOrderQuantity: number;
  stockStatus: StockStatus;
  isPublished: boolean;
}

export type UpdateProductInput = Partial<CreateProductInput>;

export interface ProductFilters {
  keyword?: string;
  categoryId?: string;
  stockStatus?: StockStatus;
  publishedOnly?: boolean;
  page?: number;
  pageSize?: number;
}

export interface PaginatedProducts {
  products: Product[];
  total: number;
  page: number;
  pageSize: number;
}
