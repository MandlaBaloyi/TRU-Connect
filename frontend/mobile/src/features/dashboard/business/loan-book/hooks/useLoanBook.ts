/**
 * useLoanBook — the whole Loan Book dashboard in one hook.
 *
 * Returns loading / error / empty as SEPARATE flags rather than one
 * blended state, because Doc 02 §2.7 requires every data-driven screen
 * to define all three distinctly, and "empty because there is nothing"
 * needs a completely different screen from "empty because a filter
 * matched nothing".
 *
 * Every query is scoped by the CURRENT user's id (see loanBookKeys.ts
 * and useCurrentUserId.ts) and gated with `enabled` until that id has
 * actually loaded -- this prevents a query firing under the wrong
 * account's cache key, or before there's any id to scope it by at all.
 */

import { useQuery } from "@tanstack/react-query";

import type { CustomerView, LoanBookSummary, LoanEntryView, LoanFilters } from "../types";
import { getCustomerViews, getLoanBookSummary, getLoanEntries } from "../api/loanBookApi";
import { hasFilters, loanBookKeys } from "./loanBookKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useLoanBook(filters?: LoanFilters) {
  const userId = useCurrentUserId();

  const summaryQuery = useQuery<LoanBookSummary>({
    queryKey: loanBookKeys.summary(userId),
    queryFn: getLoanBookSummary,
    enabled: Boolean(userId),
  });

  const entriesQuery = useQuery<LoanEntryView[]>({
    queryKey: loanBookKeys.entries(userId, filters),
    queryFn: () => getLoanEntries(filters),
    enabled: Boolean(userId),
  });

  const customersQuery = useQuery<CustomerView[]>({
    queryKey: loanBookKeys.customerViews(userId),
    queryFn: getCustomerViews,
    enabled: Boolean(userId),
  });

  const entryCount = entriesQuery.data?.length ?? 0;
  const filtersActive = hasFilters(filters);

  return {
    summary: summaryQuery.data,
    entries: entriesQuery.data ?? [],
    customers: customersQuery.data ?? [],

    isLoading: summaryQuery.isLoading || entriesQuery.isLoading,
    isRefreshing: summaryQuery.isFetching || entriesQuery.isFetching,
    isError: summaryQuery.isError || entriesQuery.isError,
    error: summaryQuery.error ?? entriesQuery.error,

    /** Nothing recorded yet — show the first-run state explaining what a
     *  Loan Book is for. */
    isEmpty: !entriesQuery.isLoading && entryCount === 0 && !filtersActive,
    /** Filters matched nothing — show "no results", not the first-run
     *  explainer, which would be confusing to someone with 200 entries. */
    isFilteredEmpty: !entriesQuery.isLoading && entryCount === 0 && filtersActive,

    refetch: () => {
      summaryQuery.refetch();
      entriesQuery.refetch();
      customersQuery.refetch();
    },
  };
}