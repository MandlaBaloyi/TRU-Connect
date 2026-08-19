/**
 * Products — React Query cache keys, centralised and user-scoped.
 *
 * EVERY KEY IS SCOPED TO A USER ID from the first draft -- a security
 * boundary, not a tidiness choice. Loan Book originally shipped with
 * an unscoped root key and had to be retrofitted after a real cross-
 * account data leak on device; Order Book and this feature both start
 * scoped so that fix never needs repeating.
 */

import type { ProductFilters } from "../types";

type UserScope = string | undefined;

function scope(userId: UserScope) {
  return ["products", userId ?? "anonymous"] as const;
}

export const productsKeys = {
  all: (userId: UserScope) => scope(userId),
  list: (userId: UserScope, filters?: ProductFilters) => [...scope(userId), "list", filters ?? {}] as const,
  detail: (userId: UserScope, productId: string) => [...scope(userId), "detail", productId] as const,
};

export function hasFilters(filters?: ProductFilters): boolean {
  if (!filters) return false;
  const listFilterActive = Boolean(filters.listFilter) && filters.listFilter !== "ALL";
  return listFilterActive || Boolean(filters.searchTerm?.trim());
}
