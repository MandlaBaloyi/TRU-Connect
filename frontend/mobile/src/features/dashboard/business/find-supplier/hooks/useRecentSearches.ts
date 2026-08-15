import { useQuery } from "@tanstack/react-query";

import { getRecentSearches } from "../services/supplierSearchService";

export function useRecentSearches() {
  const query = useQuery({
    queryKey: ["findSupplier", "recent"],
    queryFn: getRecentSearches,
    // Always refetch on mount — this screen is revisited right after
    // viewing a supplier profile (which just recorded a new recent
    // entry), so a cached/stale read here would miss it.
    staleTime: 0,
  });
  return { recentSearches: query.data ?? [], isLoading: query.isLoading };
}
