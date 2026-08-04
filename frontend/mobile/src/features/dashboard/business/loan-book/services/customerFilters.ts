/**
 * Loan Book — customer-level filtering and sorting. PURE.
 *
 * WHY THIS IS SEPARATE FROM loanFilters.ts: that file filters individual
 * LoanEntryView rows. This file filters CustomerView rows — the unit the
 * main Loan Book screen now lists, per the "customer account, not
 * transaction feed" redesign (a business owner thinks "Mandla owes me
 * R510", not "there are two rows for Mandla").
 *
 * STATUS SEMANTICS AT CUSTOMER LEVEL — deliberately different from
 * entry-level, since "a customer" doesn't have a single status the way
 * one purchase does:
 *   OUTSTANDING -> customer has at least one open (unpaid) entry
 *   OVERDUE     -> customer has at least one OVERDUE entry
 *   PAID        -> customer has zero outstanding across every entry
 * "All" includes every customer regardless, including fully-settled
 * ones — matching how the entry-level "All" filter already includes
 * paid entries rather than hiding history.
 */

import type { CustomerView, LoanStatus } from "../types";
import { normalisePhone } from "./loanValidation";

export type CustomerSortOption = "RECENT" | "HIGHEST_OWED" | "LOWEST_OWED" | "MOST_OVERDUE";

export interface CustomerFilters {
  status?: LoanStatus;
  searchTerm?: string;
  sortBy?: CustomerSortOption;
}

function matchesStatus(view: CustomerView, status?: LoanStatus): boolean {
  if (!status) return true;
  switch (status) {
    case "OVERDUE":
      return view.hasOverdue;
    case "PAID":
      return view.totalOutstanding === 0;
    case "OUTSTANDING":
      return view.openEntryCount > 0;
    default:
      return true;
  }
}

function matchesSearch(view: CustomerView, term?: string): boolean {
  if (!term || term.trim().length === 0) return true;
  const needle = term.trim().toLowerCase();
  const needlePhone = normalisePhone(needle);
  const nameMatch = view.customer.name.toLowerCase().includes(needle);
  const phoneMatch = view.customer.phone
    ? normalisePhone(view.customer.phone).includes(needlePhone)
    : false;
  return nameMatch || phoneMatch;
}

export function applyCustomerFilters(
  customers: CustomerView[],
  filters?: CustomerFilters
): CustomerView[] {
  if (!filters) return sortCustomerViews(customers, "RECENT");

  const filtered = customers.filter(
    (view) => matchesStatus(view, filters.status) && matchesSearch(view, filters.searchTerm)
  );
  return sortCustomerViews(filtered, filters.sortBy ?? "RECENT");
}

export function sortCustomerViews(
  customers: CustomerView[],
  sortBy: CustomerSortOption
): CustomerView[] {
  const sorted = [...customers];

  switch (sortBy) {
    case "RECENT":
      return sorted.sort((a, b) => {
        const aTime = a.customer.lastTransactionAt ? new Date(a.customer.lastTransactionAt).getTime() : 0;
        const bTime = b.customer.lastTransactionAt ? new Date(b.customer.lastTransactionAt).getTime() : 0;
        return bTime - aTime;
      });
    case "HIGHEST_OWED":
      return sorted.sort((a, b) => b.totalOutstanding - a.totalOutstanding);
    case "LOWEST_OWED":
      return sorted.sort((a, b) => a.totalOutstanding - b.totalOutstanding);
    case "MOST_OVERDUE":
      // Overdue customers first; within each group, larger balances first
      // — a reasonable proxy for "worst" without needing a new aggregate
      // field on CustomerView just for this ordering.
      return sorted.sort((a, b) => {
        if (a.hasOverdue !== b.hasOverdue) return a.hasOverdue ? -1 : 1;
        return b.totalOutstanding - a.totalOutstanding;
      });
    default:
      return sorted;
  }
}

export const CUSTOMER_SORT_LABELS: Record<CustomerSortOption, string> = {
  RECENT: "Most recent",
  HIGHEST_OWED: "Highest owed",
  LOWEST_OWED: "Lowest owed",
  MOST_OVERDUE: "Most overdue",
};
