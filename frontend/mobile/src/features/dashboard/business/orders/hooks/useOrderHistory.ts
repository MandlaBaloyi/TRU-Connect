import { useQuery } from "@tanstack/react-query";

import * as ordersService from "../services/ordersService";

export function useOrderHistory(supplierId: string) {
  const query = useQuery({
    queryKey: ["orders", "history", supplierId],
    queryFn: () => ordersService.getOrderHistory(supplierId),
    enabled: Boolean(supplierId),
  });

  return {
    orders: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
