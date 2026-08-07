import { useQuery } from "@tanstack/react-query";

import type { DailyRevenueEntry } from "../types";
import { getDailyRevenue } from "../api/orderBookApi";
import { orderBookKeys } from "./orderBookKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useDailyRevenue() {
  const userId = useCurrentUserId();

  const query = useQuery<DailyRevenueEntry[]>({
    queryKey: orderBookKeys.dailyRevenue(userId),
    queryFn: getDailyRevenue,
    enabled: Boolean(userId),
  });

  return {
    entries: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
