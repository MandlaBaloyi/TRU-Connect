/**
 * Inventory — React Query cache keys, user-scoped from the first
 * draft. Same reasoning as products/hooks/productsKeys.ts's own
 * docstring: Loan Book shipped unscoped once and had to be retrofitted
 * after a real cross-account leak; every feature since starts scoped.
 */

import type { InventoryFilters } from "../types";

type UserScope = string | undefined;

function scope(userId: UserScope) {
  return ["inventory", userId ?? "anonymous"] as const;
}

export const inventoryKeys = {
  all: (userId: UserScope) => scope(userId),
  list: (userId: UserScope, filters?: InventoryFilters) => [...scope(userId), "list", filters ?? {}] as const,
  detail: (userId: UserScope, productId: string) => [...scope(userId), "detail", productId] as const,
  summary: (userId: UserScope) => [...scope(userId), "summary"] as const,
};
