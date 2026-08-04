/**
 * Loan Book — mapping between storage records and what screens render.
 *
 * TWO JOBS:
 *
 * 1. ASSEMBLY. Takes raw records plus the pure algorithms and produces
 *    the view models screens actually consume (LoanEntryView,
 *    CustomerView, LoanBookSummary). Screens never derive anything
 *    themselves (feature spec: "Screens orchestrate. They do not
 *    calculate.").
 *
 * 2. WIRE FORMAT ISOLATION. When the Flask backend arrives, its JSON is
 *    snake_case (original_amount, sale_date, is_settled) while these
 *    types are camelCase. THIS FILE is the only place that will know —
 *    the same role authService.ts already plays for auth. Adding that
 *    translation later means editing one file, not every hook.
 *
 * MONEY FORMATTING also lives here, so "R 1 250.00" is produced in
 * exactly one place. Doc 02 §6: "Money amounts use a consistent format
 * and are visually emphasised wherever they represent an outstanding
 * obligation."
 */

import type {
  Cents,
  Customer,
  CustomerView,
  LoanBookSummary,
  LoanEntry,
  LoanEntryView,
  Payment,
} from "../types";
import {
  calculateCollectedInPeriod,
  calculateOutstanding,
  findLastPaymentDate,
  sumPayments,
} from "../algorithms/balanceCalculator";
import {
  calculateAgeInDays,
  calculateDaysOverdue,
  DEFAULT_OVERDUE_THRESHOLD_DAYS,
  determineStatus,
} from "../algorithms/agingCalculator";

/**
 * Build the view for one entry — the single place statuses and balances
 * are derived, so every screen showing the same entry shows identical
 * numbers.
 */
export function toLoanEntryView(
  entry: LoanEntry,
  payments: Payment[],
  thresholdDays: number = DEFAULT_OVERDUE_THRESHOLD_DAYS,
  now: Date = new Date()
): LoanEntryView {
  const entryPayments = payments.filter((p) => p.loanEntryId === entry.id);
  return {
    entry,
    payments: [...entryPayments].sort(
      (a, b) => new Date(b.paidAt).getTime() - new Date(a.paidAt).getTime()
    ),
    outstandingAmount: calculateOutstanding(entry, entryPayments),
    amountPaid: sumPayments(entryPayments),
    status: determineStatus(entry, entryPayments, thresholdDays, now),
    ageInDays: calculateAgeInDays(entry, now),
    daysOverdue: calculateDaysOverdue(entry, entryPayments, thresholdDays, now),
  };
}

/** Build views for many entries at once. */
export function toLoanEntryViews(
  entries: LoanEntry[],
  payments: Payment[],
  thresholdDays: number = DEFAULT_OVERDUE_THRESHOLD_DAYS,
  now: Date = new Date()
): LoanEntryView[] {
  return entries.map((entry) => toLoanEntryView(entry, payments, thresholdDays, now));
}

/** Build the per-customer rollup shown on the customer screen. */
export function toCustomerView(
  customer: Customer,
  entries: LoanEntry[],
  payments: Payment[],
  thresholdDays: number = DEFAULT_OVERDUE_THRESHOLD_DAYS,
  now: Date = new Date()
): CustomerView {
  const customerEntries = entries.filter((e) => e.customerId === customer.id);
  const views = toLoanEntryViews(customerEntries, payments, thresholdDays, now);
  const customerPayments = payments.filter((p) =>
    customerEntries.some((e) => e.id === p.loanEntryId)
  );

  return {
    customer,
    entries: views.sort(
      (a, b) => new Date(b.entry.saleDate).getTime() - new Date(a.entry.saleDate).getTime()
    ),
    totalOutstanding: views.reduce((total, view) => total + view.outstandingAmount, 0),
    totalOriginal: customerEntries.reduce((total, entry) => total + entry.originalAmount, 0),
    openEntryCount: views.filter((view) => view.outstandingAmount > 0).length,
    hasOverdue: views.some((view) => view.status === "OVERDUE"),
    lastPaymentAt: findLastPaymentDate(customerPayments),
  };
}

/**
 * The dashboard headline numbers.
 *
 * `customersOwingCount` counts CUSTOMERS, not entries — "18 customers
 * owe you money" is the number a shop owner actually thinks in, whereas
 * "31 open entries" is a database fact about rows.
 */
export function toLoanBookSummary(
  entries: LoanEntry[],
  payments: Payment[],
  thresholdDays: number = DEFAULT_OVERDUE_THRESHOLD_DAYS,
  now: Date = new Date()
): LoanBookSummary {
  const views = toLoanEntryViews(entries, payments, thresholdDays, now);
  const openViews = views.filter((view) => view.outstandingAmount > 0);
  const overdueViews = views.filter((view) => view.status === "OVERDUE");

  return {
    totalOutstanding: openViews.reduce((total, view) => total + view.outstandingAmount, 0),
    customersOwingCount: new Set(openViews.map((view) => view.entry.customerId)).size,
    overdueCount: overdueViews.length,
    overdueAmount: overdueViews.reduce((total, view) => total + view.outstandingAmount, 0),
    collectedLast30Days: calculateCollectedInPeriod(payments, 30, now),
  };
}

// ---------------------------------------------------------------------------
// Money formatting — one place, one format
// ---------------------------------------------------------------------------

/**
 * "R 1 250.00" — South African convention uses a space as the thousands
 * separator, not a comma.
 */
export function formatCents(cents: Cents): string {
  const isNegative = cents < 0;
  const absolute = Math.abs(cents);
  const rands = Math.floor(absolute / 100);
  const remainder = absolute % 100;
  const grouped = rands.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return `${isNegative ? "-" : ""}R ${grouped}.${remainder.toString().padStart(2, "0")}`;
}

/** Compact form for tight spaces: "R 1 250" — drops cents when they're
 *  zero, which is the common case for round cash amounts. */
export function formatCentsCompact(cents: Cents): string {
  if (cents % 100 === 0) {
    const rands = Math.floor(Math.abs(cents) / 100);
    const grouped = rands.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    return `${cents < 0 ? "-" : ""}R ${grouped}`;
  }
  return formatCents(cents);
}

/**
 * Parse typed rands into integer cents.
 *
 * Accepts "48.50", "48,50" (comma decimal is common locally), "R48.50",
 * and "1 250.00". Returns null on anything unparseable so the caller can
 * show a validation message rather than silently recording a wrong
 * amount.
 */
export function parseRandsToCents(input: string): Cents | null {
  const cleaned = input
    .replace(/[R\s]/gi, "")
    .replace(",", ".")
    .trim();
  if (cleaned.length === 0) return null;
  if (!/^\d*\.?\d*$/.test(cleaned)) return null;
  const rands = Number.parseFloat(cleaned);
  if (Number.isNaN(rands)) return null;
  // Round rather than truncate: 48.555 → 4856, not 4855.
  return Math.round(rands * 100);
}
