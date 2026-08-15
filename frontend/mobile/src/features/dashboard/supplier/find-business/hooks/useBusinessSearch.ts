/**
 * Debounced search — mirrors business/find-supplier/hooks/
 * useSupplierSearch.ts exactly.
 */
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { searchBusinesses } from "../services/businessSearchService";

const DEBOUNCE_MS = 400;

export function useBusinessSearch(query: string) {
  const [debounced, setDebounced] = useState(query);

  useEffect(() => {
    const handle = setTimeout(() => setDebounced(query), DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [query]);

  const trimmed = debounced.trim();

  const result = useQuery({
    queryKey: ["findBusiness", "search", trimmed],
    queryFn: () => searchBusinesses(trimmed),
    enabled: trimmed.length >= 2,
  });

  return {
    results: result.data ?? [],
    isSearching: result.isFetching,
    isError: result.isError,
    hasQuery: trimmed.length >= 2,
    isEmpty: result.isSuccess && trimmed.length >= 2 && result.data.length === 0,
  };
}
