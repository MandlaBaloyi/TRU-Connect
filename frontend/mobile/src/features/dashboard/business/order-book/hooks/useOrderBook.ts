/**
 * useOrderBook — the whole Order Book queue in one hook.
 *
 * Loading / error / empty are separate flags (never blended), same
 * reasoning as useLoanBook.ts: "empty because nothing's been ordered"
 * needs a different screen from "empty because a filter matched
 * nothing". Every query is gated on the current user id having loaded,
 * so nothing can fire under the wrong account's cache key.
 */

import { useQuery } from "@tanstack/react-query";

import type { OrderBookSummary, OrderFilters, OrderView } from "../types";
import { getOrderBookSummary, getOrders } from "../api/orderBookApi";
import { hasFilters, orderBookKeys } from "./orderBookKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useOrderBook(filters?: OrderFilters) {
  const userId = useCurrentUserId();

  const summaryQuery = useQuery<OrderBookSummary>({
    queryKey: orderBookKeys.summary(userId),
    queryFn: getOrderBookSummary,
    enabled: Boolean(userId),
  });

  const ordersQuery = useQuery<OrderView[]>({
    queryKey: orderBookKeys.orders(userId, filters),
    queryFn: () => getOrders(filters),
    enabled: Boolean(userId),
  });

  const orderCount = ordersQuery.data?.length ?? 0;
  const filtersActive = hasFilters(filters);

  return {
    summary: summaryQuery.data,
    orders: ordersQuery.data ?? [],

    isLoading: summaryQuery.isLoading || ordersQuery.isLoading,
    isRefreshing: summaryQuery.isFetching || ordersQuery.isFetching,
    isError: summaryQuery.isError || ordersQuery.isError,
    error: summaryQuery.error ?? ordersQuery.error,

    isEmpty: !ordersQuery.isLoading && orderCount === 0 && !filtersActive,
    isFilteredEmpty: !ordersQuery.isLoading && orderCount === 0 && filtersActive,

    refetch: () => {
      summaryQuery.refetch();
      ordersQuery.refetch();
    },
  };
}
