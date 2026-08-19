import { useQuery } from "@tanstack/react-query";

import type { InventoryFilters, InventoryListItem } from "../types";
import { getInventoryList, getInventorySummary } from "../api/inventoryApi";
import { inventoryKeys } from "./inventoryKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useInventoryList(filters?: InventoryFilters) {
  const userId = useCurrentUserId();

  const query = useQuery<InventoryListItem[]>({
    queryKey: inventoryKeys.list(userId, filters),
    queryFn: () => getInventoryList(filters),
    enabled: Boolean(userId),
  });

  const items = query.data ?? [];
  const filtersActive = Boolean(filters?.filter && filters.filter !== "ALL") || Boolean(filters?.searchTerm?.trim());

  return {
    items,
    itemCount: items.length,
    isLoading: query.isLoading,
    isRefreshing: query.isFetching,
    isError: query.isError,
    error: query.error,
    isEmpty: !query.isLoading && items.length === 0 && !filtersActive,
    isFilteredEmpty: !query.isLoading && items.length === 0 && filtersActive,
    refetch: query.refetch,
  };
}

export function useInventorySummary() {
  const userId = useCurrentUserId();

  const query = useQuery({
    queryKey: inventoryKeys.summary(userId),
    queryFn: () => getInventorySummary(),
    enabled: Boolean(userId),
  });

  return { summary: query.data, isLoading: query.isLoading };
}
