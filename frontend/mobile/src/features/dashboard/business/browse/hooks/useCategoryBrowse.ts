import { useQuery } from "@tanstack/react-query";

import { browseCategory } from "../services/browseService";

export function useCategoryBrowse(category?: string, search?: string) {
  const result = useQuery({
    // CATEGORY AND SEARCH IN THE KEY, so switching either is a real
    // fetch rather than a cached answer to a different question.
    queryKey: ["catalogue", "browse", category ?? null, search ?? null],
    queryFn: () => browseCategory({ category, search }),
    enabled: Boolean(category || search),
  });

  return {
    products: result.data?.products ?? [],
    hasMore: result.data?.hasMore ?? false,
    isLoading: result.isLoading,
    isError: result.isError,
    refetch: result.refetch,
  };
}
