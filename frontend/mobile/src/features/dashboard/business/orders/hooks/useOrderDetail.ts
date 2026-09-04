import { useQuery } from "@tanstack/react-query";

import * as ordersService from "../services/ordersService";

export function useOrderDetail(supplierId: string, orderId: string | null) {
  const query = useQuery({
    queryKey: ["orders", "detail", supplierId, orderId],
    queryFn: () => ordersService.getOrderDetail(supplierId, orderId as string),
    enabled: Boolean(supplierId) && Boolean(orderId),
  });

  return {
    order: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
  };
}
