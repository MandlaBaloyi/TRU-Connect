/**
 * Order Book — daily revenue grouping. PURE.
 * Groups COMPLETED orders by the calendar day they were completed and
 * sums their totals. Cancelled and pending orders never contribute —
 * this is "money actually made", not "money on the books".
 */

import type { DailyRevenueEntry, Order } from "../types";

/** "YYYY-MM-DD" in local time — a calendar date, not a UTC slice, so a
 *  9pm order lands on the day the shop owner actually experienced it.
 *  Exported because order numbering (mockOrderBookApi.ts) needs the
 *  exact same "what day is this" rule as revenue grouping does — two
 *  different day-boundary definitions would make "today's orders" and
 *  "today's revenue" disagree with each other. */
export function toDateKey(iso: string): string {
  const date = new Date(iso);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/** Builds the day-by-day revenue list, newest day first. Orders sitting
 *  in Trash are excluded — cleared money still happened, but Trash is
 *  reserved for its own screen, not folded into this history. */
export function calculateDailyRevenue(orders: Order[]): DailyRevenueEntry[] {
  const totals = new Map<string, DailyRevenueEntry>();

  orders
    .filter((order) => order.status === "COMPLETED" && order.completedAt && !order.deletedAt)
    .forEach((order) => {
      const key = toDateKey(order.completedAt as string);
      const existing = totals.get(key);
      if (existing) {
        existing.totalCents += order.total;
        existing.orderCount += 1;
      } else {
        totals.set(key, { date: key, totalCents: order.total, orderCount: 1 });
      }
    });

  return Array.from(totals.values()).sort((a, b) => (a.date < b.date ? 1 : -1));
}

/** "Today" / "Yesterday" / "3 Aug 2026" — same day-labelling rule used
 *  on the History screen, so Balances reads consistently with it. */
export function formatRevenueDayLabel(dateKey: string): string {
  const [year, month, day] = dateKey.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  const sameDay = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  if (sameDay(date, today)) return "Today";
  if (sameDay(date, yesterday)) return "Yesterday";
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

/** Today's entry, or a zeroed placeholder if nothing's been completed
 *  yet — TodayBalanceCard always has something to render, never an
 *  undefined check of its own. */
export function getTodayEntry(entries: DailyRevenueEntry[], now: Date = new Date()): DailyRevenueEntry {
  const todayKey = toDateKey(now.toISOString());
  return entries.find((entry) => entry.date === todayKey) ?? { date: todayKey, totalCents: 0, orderCount: 0 };
}
