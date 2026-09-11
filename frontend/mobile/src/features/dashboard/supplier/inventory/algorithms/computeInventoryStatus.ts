/**
 * computeInventoryStatus — the core rule Inventory exists to enforce:
 * the supplier manages quantity, TruConnect manages status. Order of
 * checks matters: zero-or-below is OUT_OF_STOCK even if the threshold
 * is also 0 (a threshold of 0 doesn't mean "never low stock").
 */

import type { InventoryItem, InventoryStatus } from "../types";

export function computeAvailableQuantity(item: Pick<InventoryItem, "quantityOnHand" | "quantityReserved">): number {
  return Math.max(0, item.quantityOnHand - item.quantityReserved);
}

export function computeInventoryStatus(
  item: Pick<InventoryItem, "quantityOnHand" | "lowStockThreshold">
): InventoryStatus {
  if (item.quantityOnHand <= 0) return "OUT_OF_STOCK";
  if (item.quantityOnHand <= item.lowStockThreshold) return "LOW_STOCK";
  return "IN_STOCK";
}
