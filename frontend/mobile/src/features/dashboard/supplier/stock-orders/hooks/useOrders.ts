import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import * as stockOrdersService from "../services/stockOrdersService";
import type { SortOrder, StockOrderStatus } from "../types";

/** Powers all three tabs -- New, Approved, Declined -- all genuinely
 *  plain, same shape for each. sortOrder is applied client-side, not
 *  sent to the backend -- every tab's own real query already returns
 *  newest-first, so "oldest first" is just a reverse, not a second
 *  round trip. */
export function useOrders(status: StockOrderStatus, sortOrder: SortOrder = "NEWEST") {
  const query = useQuery({
    queryKey: ["supplier", "stock-orders", status],
    queryFn: () => stockOrdersService.getOrders(status),
    staleTime: 0, // same reasoning as notifications' own list -- a real order queue must never show stale data
  });

  const orders = useMemo(() => {
    const data = query.data ?? [];
    return sortOrder === "OLDEST" ? [...data].reverse() : data;
  }, [query.data, sortOrder]);

  return {
    orders,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    isRefetching: query.isRefetching,
  };
}
