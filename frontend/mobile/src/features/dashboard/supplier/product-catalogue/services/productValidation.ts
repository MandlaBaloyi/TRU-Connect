import { z } from 'zod';

/**
 * Product form validation.
 *
 * Enforces Document 06 §4 business rules:
 *   - a product must belong to exactly one category
 *   - name, description, price, unit, minimum order quantity, and stock
 *     status are all required
 */
export const productSchema = z.object({
  categoryId: z.string().min(1, 'Please select a category'),
  name: z.string().min(3, 'Product name must be at least 3 characters').max(120),
  description: z
    .string()
    .min(10, 'Description must be at least 10 characters')
    .max(2000),
  price: z.coerce.number().positive('Price must be greater than 0'),
  unit: z.string().min(1, 'Please specify a unit (e.g. each, case, kg)'),
  minimumOrderQuantity: z.coerce
    .number()
    .int()
    .min(1, 'Minimum order quantity must be at least 1'),
  stockStatus: z.enum(['in_stock', 'low_stock', 'out_of_stock']),
  isPublished: z.boolean(),
  bulkPricingRules: z
    .array(
      z.object({
        minQuantity: z.coerce.number().int().min(1),
        price: z.coerce.number().positive(),
      }),
    )
    .optional(),
});

export type ProductFormValues = z.infer<typeof productSchema>;

/**
 * Bulk pricing tiers must have distinct, ascending minimum quantities with
 * strictly decreasing prices (the more you buy, the cheaper the unit
 * price) — not enforced by the zod schema itself since it depends on
 * relationships between array items.
 */
export function validateBulkPricingTiers(
  tiers: { minQuantity: number; price: number }[],
): string | null {
  const sorted = [...tiers].sort((a, b) => a.minQuantity - b.minQuantity);
  for (let i = 1; i < sorted.length; i += 1) {
    if (sorted[i].minQuantity === sorted[i - 1].minQuantity) {
      return 'Bulk pricing tiers must have distinct minimum quantities';
    }
    if (sorted[i].price >= sorted[i - 1].price) {
      return 'Bulk pricing tiers must decrease in price as quantity increases';
    }
  }
  return null;
}
