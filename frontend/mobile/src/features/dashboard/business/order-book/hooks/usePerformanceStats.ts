import { useMemo, useState } from "react";

import type { PerformancePeriod } from "../types";
import { calculatePerformanceStats } from "../algorithms/performanceStats";
import { useDailyRevenue } from "./useDailyRevenue";

export function usePerformanceStats(initialPeriod: PerformancePeriod = "7D") {
  const { entries, isLoading, isError, refetch } = useDailyRevenue();
  const [period, setPeriod] = useState<PerformancePeriod>(initialPeriod);

  const stats = useMemo(() => calculatePerformanceStats(entries, period), [entries, period]);

  return { stats, period, setPeriod, isLoading, isError, refetch };
}
