/**
 * Order Book — trash retention. PURE.
 * Same rule and same honest limitation as loan-book/algorithms/trashRetention.ts:
 * computed live on read, nothing purges in the background, resets with
 * app reload same as the rest of this feature's mock data. Kept as its
 * own copy rather than a cross-feature import — see types.ts docstring.
 */

import type { IsoDateString } from "../types";

export const TRASH_RETENTION_DAYS = 7;

function daysSince(iso: IsoDateString, now: Date): number {
  const then = new Date(iso).getTime();
  const diffMs = now.getTime() - then;
  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

/** Whole days remaining before an item is no longer restorable. Never
 *  negative — clamps at 0 rather than counting past expiry. */
export function daysRemainingInTrash(deletedAt: IsoDateString, now: Date = new Date()): number {
  return Math.max(0, TRASH_RETENTION_DAYS - daysSince(deletedAt, now));
}

/** True once an item has aged past the retention window. */
export function isExpiredFromTrash(deletedAt: IsoDateString, now: Date = new Date()): boolean {
  return daysSince(deletedAt, now) >= TRASH_RETENTION_DAYS;
}

/** Human-readable countdown for the Trash screen. Checks expiry FIRST —
 *  same reasoning as Loan Book's version: a stale-cached item found past
 *  the window must say "Expired", never a countdown implying recovery
 *  is still possible. */
export function formatTrashCountdown(deletedAt: IsoDateString, now: Date = new Date()): string {
  if (isExpiredFromTrash(deletedAt, now)) return "Expired";
  const remaining = daysRemainingInTrash(deletedAt, now);
  if (remaining <= 1) return "Expiring today";
  return `${remaining} days left`;
}
