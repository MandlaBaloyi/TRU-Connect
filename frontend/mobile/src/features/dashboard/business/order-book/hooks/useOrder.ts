import { useQuery } from "@tanstack/react-query";

import type { OrderView } from "../types";
import { getOrder } from "../api/orderBookApi";
import { orderBookKeys } from "./orderBookKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useOrder(orderId: string | undefined) {
  const userId = useCurrentUserId();

  const query = useQuery<OrderView | null>({
    queryKey: orderBookKeys.order(userId, orderId ?? ""),
    queryFn: () => getOrder(orderId as string),
    enabled: Boolean(userId) && Boolean(orderId),
  });

  return {
    view: query.data ?? undefined,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
