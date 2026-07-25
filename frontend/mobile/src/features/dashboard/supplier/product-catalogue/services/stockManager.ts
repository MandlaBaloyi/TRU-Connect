import type { Product, StockStatus } from '../types';

interface StockStatusMeta {
  label: string;
  colorRole: 'success' | 'warning' | 'danger';
}

const STOCK_STATUS_META: Record<StockStatus, StockStatusMeta> = {
  in_stock: { label: 'In Stock', colorRole: 'success' },
  low_stock: { label: 'Low Stock', colorRole: 'warning' },
  out_of_stock: { label: 'Out of Stock', colorRole: 'danger' },
};

export function getStockStatusMeta(status: StockStatus): StockStatusMeta {
  return STOCK_STATUS_META[status];
}

export const STOCK_STATUS_OPTIONS: { value: StockStatus; label: string }[] = (
  Object.keys(STOCK_STATUS_META) as StockStatus[]
).map((value) => ({ value, label: STOCK_STATUS_META[value].label }));

/**
 * Document 06 §4: a product needs its core fields complete before it can
 * be published. Draft products may be incomplete; published products may
 * not.
 */
export function canPublish(
  product: Pick<Product, 'name' | 'categoryId' | 'price' | 'unit' | 'minimumOrderQuantity'>,
): boolean {
  return Boolean(
    product.name?.trim() &&
      product.categoryId &&
      product.price > 0 &&
      product.unit?.trim() &&
      product.minimumOrderQuantity >= 1,
  );
}

/**
 * Document 06 §4: out_of_stock products remain visible but are excluded
 * from "Popular Products" ranking. Kept here, next to the stock status
 * definitions, so discovery-side features can reuse the same rule.
 */
export function isExcludedFromPopularRanking(status: StockStatus): boolean {
  return status === 'out_of_stock';
}
