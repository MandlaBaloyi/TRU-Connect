import { useQuery } from "@tanstack/react-query";

import type { OrderHistoryEvent } from "../types";
import { getOrderHistory } from "../api/orderBookApi";
import { orderBookKeys } from "./orderBookKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export const historyKeys = orderBookKeys;

export function useOrderHistory() {
  const userId = useCurrentUserId();

  const query = useQuery<OrderHistoryEvent[]>({
    queryKey: orderBookKeys.history(userId),
    queryFn: getOrderHistory,
    enabled: Boolean(userId),
  });

  return {
    events: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
