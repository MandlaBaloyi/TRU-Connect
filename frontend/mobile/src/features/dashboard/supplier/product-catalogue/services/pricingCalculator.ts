import type { BulkPricingTier, Product } from '../types';

export function getEffectiveUnitPrice(
  product: Pick<Product, 'price' | 'bulkPricingRules'>,
  quantity: number,
): number {
  const applicable = [...(product.bulkPricingRules ?? [])]
    .filter((tier) => quantity >= tier.minQuantity)
    .sort((a, b) => b.minQuantity - a.minQuantity)[0];
  return applicable ? applicable.price : product.price;
}

export function getLineTotal(
  product: Pick<Product, 'price' | 'bulkPricingRules'>,
  quantity: number,
): number {
  return getEffectiveUnitPrice(product, quantity) * quantity;
}

export function formatPrice(amount: number, currency = 'ZAR'): string {
  try {
    return new Intl.NumberFormat('en-ZA', { style: 'currency', currency }).format(amount);
  } catch {
    return `R${amount.toFixed(2)}`;
  }
}

export function getPriceRangeLabel(product: Pick<Product, 'price' | 'bulkPricingRules'>): string {
  if (!product.bulkPricingRules?.length) return formatPrice(product.price);
  const lowest = Math.min(product.price, ...product.bulkPricingRules.map((tier) => tier.price));
  return `${formatPrice(lowest)} \u2013 ${formatPrice(product.price)}`;
}

export function sortTiersByQuantity(tiers: BulkPricingTier[]): BulkPricingTier[] {
  return [...tiers].sort((a, b) => a.minQuantity - b.minQuantity);
}
