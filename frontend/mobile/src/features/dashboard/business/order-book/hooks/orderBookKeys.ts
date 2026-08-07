/**
 * Order Book — React Query cache keys, centralised and user-scoped.
 *
 * EVERY KEY IS SCOPED TO A USER ID from the first draft — this is a
 * security boundary, not a tidiness choice. Loan Book originally shipped
 * with an unscoped ["loanBook"] root and had to be retrofitted after a
 * real cross-account data leak on device (see order_book_handoff.md
 * §5a). Order Book starts scoped so that fix never needs repeating.
 */

import type { OrderFilters } from "../types";

type UserScope = string | undefined;

function scope(userId: UserScope) {
  return ["orderBook", userId ?? "anonymous"] as const;
}

export const orderBookKeys = {
  all: (userId: UserScope) => scope(userId),
  summary: (userId: UserScope) => [...scope(userId), "summary"] as const,
  orders: (userId: UserScope, filters?: OrderFilters) =>
    [...scope(userId), "orders", filters ?? {}] as const,
  order: (userId: UserScope, orderId: string) => [...scope(userId), "order", orderId] as const,
  customerSearch: (userId: UserScope, term: string) =>
    [...scope(userId), "customerSearch", term] as const,
  history: (userId: UserScope) => [...scope(userId), "history"] as const,
  trash: (userId: UserScope) => [...scope(userId), "trash"] as const,
  dailyRevenue: (userId: UserScope) => [...scope(userId), "dailyRevenue"] as const,
  autoClearDuration: (userId: UserScope) => [...scope(userId), "autoClearDuration"] as const,
};

export function hasFilters(filters?: OrderFilters): boolean {
  if (!filters) return false;
  return Boolean(filters.status || filters.searchTerm?.trim());
}
