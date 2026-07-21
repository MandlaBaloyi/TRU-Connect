/**
 * Cross-cutting dashboard types shared by both Business and Supplier
 * dashboards. Role-specific shapes live in
 * features/dashboard/{business,supplier}/types.ts instead.
 */
export interface TrendValue {
  percent: number;
  direction: "up" | "down";
}

export interface ActivityEntry {
  id: string;
  iconKey: string;
  title: string;
  timestamp: string;
}
