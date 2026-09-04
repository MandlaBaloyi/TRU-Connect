import { useQuery } from "@tanstack/react-query";

import * as stockOrdersService from "../services/stockOrdersService";

export function useOrderDetail(orderId: string) {
  const query = useQuery({
    queryKey: ["supplier", "stock-orders", "detail", orderId],
    queryFn: () => stockOrdersService.getOrderDetail(orderId),
    enabled: Boolean(orderId),
    staleTime: 0,
  });

  return {
    order: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
