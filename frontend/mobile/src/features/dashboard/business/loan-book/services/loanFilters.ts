/**
 * Loan Book — filtering and sorting. PURE.
 *
 * Kept out of both the repository and the hooks deliberately:
 *
 *   - Not in the repository, because when SQLite arrives some of this
 *     becomes a WHERE clause and some stays in JS. Having the semantics
 *     defined here as pure functions means the SQLite implementation has
 *     something exact to match, rather than reverse-engineering
 *     behaviour from a hook.
 *
 *   - Not in the hooks, because filtering is a rule, not a React
 *     concern, and rules living in hooks can't be tested without
 *     rendering anything.
 */

import type { Customer, LoanEntryView, LoanFilters, LoanSortOption } from "../types";
import { normalisePhone } from "./loanValidation";

/**
 * Apply filters and sorting to a list of entry views.
 *
 * Needs the customer list because search matches on customer NAME, which
 * lives on a different record than the entry. A shop owner searching
 * "Thandi" is looking for a person, not a transaction.
 */
export function applyFilters(
  views: LoanEntryView[],
  customers: Customer[],
  filters?: LoanFilters
): LoanEntryView[] {
  if (!filters) return sortViews(views, "NEWEST");

  let result = views;

  if (filters.status) {
    result = result.filter((view) => view.status === filters.status);
  }

  if (filters.customerId) {
    result = result.filter((view) => view.entry.customerId === filters.customerId);
  }

  if (filters.searchTerm && filters.searchTerm.trim().length > 0) {
    const needle = filters.searchTerm.trim().toLowerCase();
    const needlePhone = normalisePhone(needle);

    const matchingCustomerIds = new Set(
      customers
        .filter((customer) => {
          const nameMatch = customer.name.toLowerCase().includes(needle);
          const phoneMatch = customer.phone
            ? normalisePhone(customer.phone).includes(needlePhone)
            : false;
          return nameMatch || phoneMatch;
        })
        .map((customer) => customer.id)
    );

    result = result.filter(
      (view) =>
        matchingCustomerIds.has(view.entry.customerId) ||
        // Also match the entry's own description — "paraffin" is a
        // reasonable thing to search for.
        (view.entry.description?.toLowerCase().includes(needle) ?? false)
    );
  }

  return sortViews(result, filters.sortBy ?? "NEWEST");
}

export function sortViews(views: LoanEntryView[], sortBy: LoanSortOption): LoanEntryView[] {
  const sorted = [...views];

  switch (sortBy) {
    case "NEWEST":
      return sorted.sort(
        (a, b) => new Date(b.entry.saleDate).getTime() - new Date(a.entry.saleDate).getTime()
      );
    case "OLDEST":
      return sorted.sort(
        (a, b) => new Date(a.entry.saleDate).getTime() - new Date(b.entry.saleDate).getTime()
      );
    case "HIGHEST_AMOUNT":
      return sorted.sort((a, b) => b.outstandingAmount - a.outstandingAmount);
    case "LOWEST_AMOUNT":
      return sorted.sort((a, b) => a.outstandingAmount - b.outstandingAmount);
    case "MOST_OVERDUE":
      return sorted.sort((a, b) => b.daysOverdue - a.daysOverdue);
    default:
      // Exhaustiveness guard: adding a LoanSortOption without handling it
      // here returns a stable order rather than an empty or scrambled
      // list. Same defensive-default reasoning as LoanStatusBadge.
      return sorted;
  }
}

/** Human-readable labels for the filter/sort UI. Plain words, not
 *  database vocabulary (Doc 02 §14). */
export const SORT_LABELS: Record<LoanSortOption, string> = {
  NEWEST: "Newest first",
  OLDEST: "Oldest first",
  HIGHEST_AMOUNT: "Highest amount",
  LOWEST_AMOUNT: "Lowest amount",
  MOST_OVERDUE: "Most overdue",
};

export const STATUS_LABELS = {
  OUTSTANDING: "Unpaid",
  PAID: "Paid",
  OVERDUE: "Overdue",
} as const;
