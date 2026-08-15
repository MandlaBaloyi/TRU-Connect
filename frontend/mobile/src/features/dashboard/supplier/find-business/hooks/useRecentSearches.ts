import { useQuery } from "@tanstack/react-query";

import { getRecentSearches } from "../services/businessSearchService";

export function useRecentSearches() {
  const query = useQuery({
    queryKey: ["findBusiness", "recent"],
    queryFn: getRecentSearches,
    staleTime: 0,
  });
  return { recentSearches: query.data ?? [], isLoading: query.isLoading };
}
