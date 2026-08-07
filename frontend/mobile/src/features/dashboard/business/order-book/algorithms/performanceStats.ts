/**
 * Order Book — performance stats. PURE. Rolls up DailyRevenueEntry[]
 * (already computed by dailyRevenue.ts) into the "how has business
 * been" figures for a given period. Deliberately reuses the same
 * per-day entries the TODAY card is built from, rather than
 * re-deriving totals from raw orders — one source of truth for "what
 * counts as a day's revenue".
 */

import type { DailyRevenueEntry, PerformancePeriod, PerformanceStats } from "../types";
import { PERFORMANCE_PERIOD_DAYS } from "../types";
import { toDateKey } from "./dailyRevenue";

/** Filters entries to the last N calendar days INCLUDING today, then
 *  rolls them up. Days with no completed orders simply have no entry
 *  (dailyRevenue.ts never emits a zero row), so they correctly
 *  contribute 0 to totalCents/orderCount/bestDay without special-casing. */
export function calculatePerformanceStats(
  entries: DailyRevenueEntry[],
  period: PerformancePeriod,
  now: Date = new Date()
): PerformanceStats {
  const days = PERFORMANCE_PERIOD_DAYS[period];
  const cutoff = new Date(now);
  cutoff.setDate(cutoff.getDate() - (days - 1));
  const cutoffKey = toDateKey(cutoff.toISOString());

  const inRange = entries.filter((entry) => entry.date >= cutoffKey);

  const totalCents = inRange.reduce((sum, entry) => sum + entry.totalCents, 0);
  const orderCount = inRange.reduce((sum, entry) => sum + entry.orderCount, 0);
  const bestDayCents = inRange.reduce((max, entry) => Math.max(max, entry.totalCents), 0);
  const averageDailyCents = days > 0 ? Math.round(totalCents / days) : 0;

  return { totalCents, orderCount, bestDayCents, averageDailyCents };
}
