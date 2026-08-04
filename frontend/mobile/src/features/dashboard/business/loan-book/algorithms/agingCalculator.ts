/**
 * Loan Book — loan aging and overdue determination. PURE.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt §12
 *
 * WHY AGING RATHER THAN A DUE DATE:
 * credit_ledger_entries (Doc 04 §3.5) has a sale_date and deliberately
 * no due-date column. That is not an omission — asking a shop owner to
 * pick a due date while a customer stands waiting adds a required field
 * to a flow that must complete in under 30 seconds, and Doc 02 §1.2
 * names typing as "the single largest source of friction". Informal
 * credit rarely has an agreed due date anyway; it has an expectation.
 *
 * So "overdue" is derived from age: an entry still outstanding after
 * DEFAULT_OVERDUE_THRESHOLD_DAYS is overdue. This costs the owner zero
 * extra taps and works retroactively on entries recorded before the
 * concept existed.
 *
 * The threshold is a named constant, not a literal, precisely because it
 * is expected to become a per-business setting (7/14/21/30/45/60 days).
 * Every function here accepts it as a parameter with the constant as
 * default, so making it configurable later requires no changes here.
 */

import type { IsoDateString, LoanEntry, LoanStatus, Payment } from "../types";
import { calculateOutstanding } from "./balanceCalculator";

/** Phase 1 default. Becomes a per-business setting later — see above. */
export const DEFAULT_OVERDUE_THRESHOLD_DAYS = 30;

/** Options a business may eventually choose from in settings. */
export const OVERDUE_THRESHOLD_OPTIONS = [7, 14, 21, 30, 45, 60] as const;

const MS_PER_DAY = 24 * 60 * 60 * 1000;

/**
 * Whole days elapsed since a date.
 *
 * Compares calendar days at UTC midnight rather than raw elapsed
 * milliseconds. A sale recorded at 23:50 and viewed at 00:10 the next
 * morning is 1 day old to a human, not 0 — and a shop owner counting
 * "how long has this been sitting" counts sleeps, not hours. Raw
 * millisecond division would produce the technically-correct-but-wrong
 * answer here.
 */
export function daysSince(date: IsoDateString, now: Date = new Date()): number {
  const then = new Date(date);
  const thenMidnight = Date.UTC(then.getUTCFullYear(), then.getUTCMonth(), then.getUTCDate());
  const nowMidnight = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return Math.max(0, Math.round((nowMidnight - thenMidnight) / MS_PER_DAY));
}

/** Age of an entry in whole days since the sale. */
export function calculateAgeInDays(entry: LoanEntry, now: Date = new Date()): number {
  return daysSince(entry.saleDate, now);
}

/**
 * Days past the overdue threshold. Zero when not overdue — callers can
 * therefore use a simple truthiness check without a separate boolean.
 */
export function calculateDaysOverdue(
  entry: LoanEntry,
  payments: Payment[],
  thresholdDays: number = DEFAULT_OVERDUE_THRESHOLD_DAYS,
  now: Date = new Date()
): number {
  // A settled entry is never overdue, regardless of how long it took.
  if (calculateOutstanding(entry, payments) === 0) return 0;
  const age = calculateAgeInDays(entry, now);
  return Math.max(0, age - thresholdDays);
}

/**
 * The single source of truth for an entry's status.
 *
 * Order matters: settled is checked FIRST, so an entry paid off on day
 * 90 shows as PAID rather than OVERDUE. The debt is closed; presenting
 * it as overdue would be both wrong and discouraging.
 */
export function determineStatus(
  entry: LoanEntry,
  payments: Payment[],
  thresholdDays: number = DEFAULT_OVERDUE_THRESHOLD_DAYS,
  now: Date = new Date()
): LoanStatus {
  if (calculateOutstanding(entry, payments) === 0) return "PAID";
  if (calculateDaysOverdue(entry, payments, thresholdDays, now) > 0) return "OVERDUE";
  return "OUTSTANDING";
}

/**
 * Human-readable age, for a card subtitle.
 * Plain language, no jargon (Doc 02 §14).
 */
export function formatAge(ageInDays: number): string {
  if (ageInDays === 0) return "Today";
  if (ageInDays === 1) return "Yesterday";
  if (ageInDays < 7) return `${ageInDays} days ago`;
  if (ageInDays < 14) return "Last week";
  if (ageInDays < 31) return `${Math.floor(ageInDays / 7)} weeks ago`;
  if (ageInDays < 62) return "Last month";
  return `${Math.floor(ageInDays / 30)} months ago`;
}

/**
 * Buckets for the analytics screen — how long money has been sitting
 * unpaid. Standard receivables aging, in plain words rather than the
 * usual "0-30 / 31-60 / 61-90" accountancy labels.
 */
export type AgingBucket = "CURRENT" | "OVERDUE_RECENT" | "OVERDUE_LONG" | "OVERDUE_VERY_LONG";

export function determineAgingBucket(
  entry: LoanEntry,
  payments: Payment[],
  thresholdDays: number = DEFAULT_OVERDUE_THRESHOLD_DAYS,
  now: Date = new Date()
): AgingBucket {
  const overdue = calculateDaysOverdue(entry, payments, thresholdDays, now);
  if (overdue === 0) return "CURRENT";
  if (overdue <= 30) return "OVERDUE_RECENT";
  if (overdue <= 60) return "OVERDUE_LONG";
  return "OVERDUE_VERY_LONG";
}

export const AGING_BUCKET_LABELS: Record<AgingBucket, string> = {
  CURRENT: "Not yet due",
  OVERDUE_RECENT: "Overdue",
  OVERDUE_LONG: "Overdue over a month",
  OVERDUE_VERY_LONG: "Overdue over two months",
};
