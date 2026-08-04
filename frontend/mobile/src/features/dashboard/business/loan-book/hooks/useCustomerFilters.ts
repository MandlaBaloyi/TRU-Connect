/**
 * useCustomerFilters — filter/sort state for the customer-first Loan
 * Book list. Mirrors useLoanFilters's shape, but for CustomerFilters.
 *
 * Plain component state, not React Query — no server call involved.
 */

import { useMemo, useState } from "react";

import type { LoanStatus } from "../types";
import type { CustomerFilters, CustomerSortOption } from "../services/customerFilters";

export function useCustomerFilters(initial?: CustomerFilters) {
  const [status, setStatus] = useState<LoanStatus | undefined>(initial?.status);
  const [searchTerm, setSearchTerm] = useState<string>(initial?.searchTerm ?? "");
  const [sortBy, setSortBy] = useState<CustomerSortOption>(initial?.sortBy ?? "RECENT");

  const filters = useMemo<CustomerFilters>(
    () => ({ status, searchTerm: searchTerm.trim() || undefined, sortBy }),
    [status, searchTerm, sortBy]
  );

  const activeFilterCount = useMemo(
    () => [status, searchTerm.trim() || undefined].filter(Boolean).length,
    [status, searchTerm]
  );

  return {
    filters,
    status,
    setStatus,
    searchTerm,
    setSearchTerm,
    sortBy,
    setSortBy,
    activeFilterCount,
    hasActiveFilters: activeFilterCount > 0,
    clear: () => {
      setStatus(undefined);
      setSearchTerm("");
      setSortBy("RECENT");
    },
  };
}
