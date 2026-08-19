import { useQuery } from "@tanstack/react-query";

import type { InventoryListItem } from "../types";
import { getInventoryItem } from "../api/inventoryApi";
import { inventoryKeys } from "./inventoryKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useInventoryItem(productId: string) {
  const userId = useCurrentUserId();

  const query = useQuery<InventoryListItem>({
    queryKey: inventoryKeys.detail(userId, productId),
    queryFn: () => getInventoryItem(productId),
    enabled: Boolean(userId) && Boolean(productId),
  });

  return {
    item: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
