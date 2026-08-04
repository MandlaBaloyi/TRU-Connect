/**
 * Loan Book — React Query cache keys, centralised.
 *
 * Defined in one object rather than as inline string arrays so that
 * invalidation after a write cannot silently miss a cache — a typo in an
 * inline key produces no error, just a stale screen, which is the kind
 * of bug that gets blamed on "the app being slow".
 */

import type { LoanFilters } from "../types";

export const loanBookKeys = {
  all: ["loanBook"] as const,
  summary: () => [...loanBookKeys.all, "summary"] as const,
  entries: (filters?: LoanFilters) => [...loanBookKeys.all, "entries", filters ?? {}] as const,
  entry: (entryId: string) => [...loanBookKeys.all, "entry", entryId] as const,
  customers: () => [...loanBookKeys.all, "customers"] as const,
  customerViews: () => [...loanBookKeys.all, "customerViews"] as const,
  customer: (customerId: string) => [...loanBookKeys.all, "customer", customerId] as const,
  customerSearch: (term: string) => [...loanBookKeys.all, "customerSearch", term] as const,
};

export function hasFilters(filters?: LoanFilters): boolean {
  if (!filters) return false;
  return Boolean(filters.status || filters.customerId || filters.searchTerm?.trim());
}
