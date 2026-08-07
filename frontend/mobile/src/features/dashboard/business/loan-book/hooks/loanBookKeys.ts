/**
 * Loan Book — React Query cache keys, centralised.
 *
 * Defined in one object rather than as inline string arrays so that
 * invalidation after a write cannot silently miss a cache — a typo in an
 * inline key produces no error, just a stale screen, which is the kind
 * of bug that gets blamed on "the app being slow".
 *
 * EVERY KEY IS SCOPED TO A USER ID. This is a security boundary, not a
 * tidiness choice. Previously every key descended from a shared
 * ["loanBook"] root, so account A's cached customers and B's occupied
 * the SAME cache entry. Logging out of A and into B (or back to A
 * again) meant React Query would instantly paint whatever it already
 * had under that shared key while the real request was still in flight
 * -- one business briefly seeing another business's customer names and
 * balances on screen.
 *
 * Clearing the cache on logout was tried first and is NOT sufficient on
 * its own: it depends on the logout path actually running at exactly
 * the right moment, and silently does nothing if a session ends any
 * other way (app killed, token expiry, a navigation that bypasses the
 * logout mutation). Scoping the key itself means the leak is
 * structurally impossible rather than merely cleaned up after -- B
 * cannot read A's cache entry because it is not the same entry.
 */

import type { LoanFilters } from "../types";

/** Falls back to "anonymous" rather than throwing -- a missing user id
 *  means nobody is logged in, and that state deserves its own cache
 *  bucket too, never a shared one. */
type UserScope = string | undefined;

function scope(userId: UserScope) {
  return ["loanBook", userId ?? "anonymous"] as const;
}

export const loanBookKeys = {
  all: (userId: UserScope) => scope(userId),
  summary: (userId: UserScope) => [...scope(userId), "summary"] as const,
  entries: (userId: UserScope, filters?: LoanFilters) =>
    [...scope(userId), "entries", filters ?? {}] as const,
  entry: (userId: UserScope, entryId: string) => [...scope(userId), "entry", entryId] as const,
  customers: (userId: UserScope) => [...scope(userId), "customers"] as const,
  customerViews: (userId: UserScope) => [...scope(userId), "customerViews"] as const,
  customer: (userId: UserScope, customerId: string) =>
    [...scope(userId), "customer", customerId] as const,
  customerSearch: (userId: UserScope, term: string) =>
    [...scope(userId), "customerSearch", term] as const,
};

export function hasFilters(filters?: LoanFilters): boolean {
  if (!filters) return false;
  return Boolean(filters.status || filters.customerId || filters.searchTerm?.trim());
}