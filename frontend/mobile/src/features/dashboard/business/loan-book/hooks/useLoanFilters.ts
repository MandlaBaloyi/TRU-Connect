/**
 * useLoanFilters — filter and sort state.
 *
 * Plain component state, deliberately NOT React Query: no server is
 * involved, and putting UI state in a data cache makes both harder to
 * reason about.
 */

import { useMemo, useState } from "react";

import type { LoanFilters, LoanSortOption, LoanStatus } from "../types";

export function useLoanFilters(initial?: LoanFilters) {
  const [status, setStatus] = useState<LoanStatus | undefined>(initial?.status);
  const [customerId, setCustomerId] = useState<string | undefined>(initial?.customerId);
  const [searchTerm, setSearchTerm] = useState<string>(initial?.searchTerm ?? "");
  const [sortBy, setSortBy] = useState<LoanSortOption>(initial?.sortBy ?? "NEWEST");

  const filters = useMemo<LoanFilters>(
    () => ({ status, customerId, searchTerm: searchTerm.trim() || undefined, sortBy }),
    [status, customerId, searchTerm, sortBy]
  );

  const activeFilterCount = useMemo(
    () => [status, customerId, searchTerm.trim() || undefined].filter(Boolean).length,
    [status, customerId, searchTerm]
  );

  return {
    filters,
    status,
    setStatus,
    customerId,
    setCustomerId,
    searchTerm,
    setSearchTerm,
    sortBy,
    setSortBy,
    activeFilterCount,
    hasActiveFilters: activeFilterCount > 0,
    clear: () => {
      setStatus(undefined);
      setCustomerId(undefined);
      setSearchTerm("");
      setSortBy("NEWEST");
    },
  };
}
