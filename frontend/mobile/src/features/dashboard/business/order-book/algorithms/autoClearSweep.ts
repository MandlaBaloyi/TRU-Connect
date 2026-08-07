/**
 * Order Book — auto-clear sweep. PURE decision logic only: given orders,
 * an AutoClearSetting, and which status it applies to, which orders are
 * due for Trash? Deliberately has NO knowledge of storage, timers, or
 * the mock API — those live in hooks/useAutoClearSettings.ts and
 * api/mockOrderBookApi.ts. This split means that when the real backend
 * exists, this exact function becomes the body of a scheduled job
 * (same master-scheduler pattern already used elsewhere in this
 * project) with no rewrite — only its caller changes.
 *
 * COMPLETED and CANCELLED are swept independently, each against its own
 * setting and its own timestamp (completedAt vs cancelledAt) — see
 * AutoClearScope's docstring in types.ts for why they're not shared.
 */

import type { AutoClearScope, AutoClearSetting, Order } from "../types";
import { AUTO_CLEAR_FIXED_DURATION_MS } from "../types";

/** Resolves a setting to a concrete window in ms, or null if disabled.
 *  CUSTOM with a missing/invalid hour count is treated as disabled
 *  rather than guessing — an unset custom value should never silently
 *  clear orders immediately (0ms) or never (NaN). */
export function resolveWindowMs(setting: AutoClearSetting): number | null {
  if (setting.duration === "CUSTOM") {
    if (!setting.customHours || setting.customHours <= 0) return null;
    return setting.customHours * 60 * 60 * 1000;
  }
  return AUTO_CLEAR_FIXED_DURATION_MS[setting.duration] ?? null;
}

function timestampFor(order: Order, scope: AutoClearScope): string | undefined {
  return scope === "COMPLETED" ? order.completedAt : order.cancelledAt;
}

/** Each order carries its own countdown, timed from its own
 *  completedAt/cancelledAt — not from a shared daily reset. */
export function findOrdersDueForAutoClear(
  orders: Order[],
  setting: AutoClearSetting,
  scope: AutoClearScope,
  now: Date = new Date()
): Order[] {
  const windowMs = resolveWindowMs(setting);
  if (windowMs === null) return [];

  return orders.filter((order) => {
    if (order.status !== scope || order.deletedAt) return false;
    const timestamp = timestampFor(order, scope);
    if (!timestamp) return false;
    const elapsed = now.getTime() - new Date(timestamp).getTime();
    return elapsed >= windowMs;
  });
}
