/**
 * Loan Book — trash retention. PURE.
 *
 * HONEST LIMITATION, STATED UP FRONT: this feature's data resets on
 * every app reload (a deliberate decision — no SQLite yet, see
 * README.md). "7 days" here is therefore only meaningful WITHIN one
 * continuous session; it cannot survive the user closing the app any
 * more than the rest of this feature's data can. Once real persistence
 * lands, this same logic inherits genuine cross-restart retention for
 * free — nothing here needs to change, only the repository underneath
 * it. Built honestly correct for what's actually running today, not
 * pretending to a guarantee the current architecture can't keep.
 *
 * NO BACKGROUND TIMER PURGES ANYTHING. Rather than a scheduled job
 * silently deleting expired trash (which belongs to a real backend
 * scheduler once one exists — see platform/schedulers/), expiry is
 * computed live, on read: `listDeletedCustomers()` /
 * `listDeletedEntries()` simply stop returning an item once it's past
 * the retention window. The data technically still sits in memory until
 * the next reload, but it is functionally gone — unreachable, not
 * restorable — which is the only property that actually matters to the
 * user.
 */

import { daysSince } from "./agingCalculator";
import type { IsoDateString } from "../types";

/** Matches the informal-credit-book precedent already used for the
 *  overdue threshold: a plain named constant, not a magic number,
 *  because it's expected to become configurable later. */
export const TRASH_RETENTION_DAYS = 7;

/** Whole days remaining before an item is no longer restorable.
 *  Never negative — clamps at 0 rather than counting past expiry. */
export function daysRemainingInTrash(deletedAt: IsoDateString, now: Date = new Date()): number {
  const elapsed = daysSince(deletedAt, now);
  return Math.max(0, TRASH_RETENTION_DAYS - elapsed);
}

/** True once an item has aged past the retention window. */
export function isExpiredFromTrash(deletedAt: IsoDateString, now: Date = new Date()): boolean {
  return daysSince(deletedAt, now) >= TRASH_RETENTION_DAYS;
}

/** Human-readable countdown for the Trash screen: "6 days left",
 *  "Expiring today", "Expired" — plain language, no jargon (Doc 02 §14).
 *  Checks expiry FIRST: an item found long past the window (e.g. after
 *  being reachable via a stale cached list) must say "Expired", never a
 *  countdown implying it's still recoverable. */
export function formatTrashCountdown(deletedAt: IsoDateString, now: Date = new Date()): string {
  if (isExpiredFromTrash(deletedAt, now)) return "Expired";
  const remaining = daysRemainingInTrash(deletedAt, now);
  if (remaining <= 1) return "Expiring today";
  return `${remaining} days left`;
}
