/**
 * Loan Book — balance calculation. PURE: no UI, no API, no storage.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt §12.2
 *
 * CORE RULE: outstanding is DERIVED from the payment history, never read
 * from a stored column.
 *
 * The database does carry an `outstanding_amount` column (Doc 04 §3.5),
 * and it is genuinely useful there — it lets the server sort and
 * aggregate without joining every payment row. But it is a CACHE, not
 * the truth. The truth is: original minus the sum of payments.
 *
 * Why this matters concretely: once offline sync exists, a repayment can
 * be recorded on the device and reach the server later. If a screen
 * trusted the stored column, it would show a balance that silently
 * disagrees with the payment list printed directly beneath it — and the
 * shop owner would be looking at two different numbers for the same
 * debt, with no way to tell which is right. Deriving it means the number
 * and its evidence can never contradict each other.
 *
 * This is standard accounting practice: the ledger is the truth, the
 * balance is a conclusion drawn from it.
 */

import type { Cents, LoanEntry, Payment } from "../types";

/** Sum of payments made against one entry. */
export function sumPayments(payments: Payment[]): Cents {
  return payments.reduce((total, payment) => total + payment.amount, 0);
}

/**
 * Outstanding balance for one entry.
 *
 * Clamped at zero: an overpayment (which paymentAllocation prevents, but
 * which could still arrive from a legacy record or a future sync
 * conflict) must never render as a negative debt. A shop owner seeing
 * "-R 20.00 owed" would reasonably conclude the app is broken.
 */
export function calculateOutstanding(entry: LoanEntry, payments: Payment[]): Cents {
  const paid = sumPayments(payments);
  return Math.max(0, entry.originalAmount - paid);
}

/** True once the entry is fully repaid. */
export function isFullySettled(entry: LoanEntry, payments: Payment[]): boolean {
  return calculateOutstanding(entry, payments) === 0;
}

/**
 * Total outstanding across many entries — the headline figure on the
 * dashboard ("Money Owed To You").
 *
 * Takes already-paired entries and payments rather than fetching, so it
 * stays pure and trivially testable.
 */
export function calculateTotalOutstanding(
  pairs: { entry: LoanEntry; payments: Payment[] }[]
): Cents {
  return pairs.reduce(
    (total, { entry, payments }) => total + calculateOutstanding(entry, payments),
    0
  );
}

/** Total originally extended as credit, settled or not. */
export function calculateTotalOriginal(entries: LoanEntry[]): Cents {
  return entries.reduce((total, entry) => total + entry.originalAmount, 0);
}

/**
 * Total collected within the trailing `days` window.
 *
 * Deliberately included on the dashboard alongside what's owed: a screen
 * that shows only debt is a discouraging screen, and Doc 02 §1.6 asks
 * every element to justify itself. "You collected R 1,240 this month" is
 * the one number that tells the owner the book is working.
 */
export function calculateCollectedInPeriod(
  payments: Payment[],
  days: number,
  now: Date = new Date()
): Cents {
  const cutoff = now.getTime() - days * 24 * 60 * 60 * 1000;
  return payments
    .filter((payment) => new Date(payment.paidAt).getTime() >= cutoff)
    .reduce((total, payment) => total + payment.amount, 0);
}

/**
 * The most recent payment timestamp, or undefined if none.
 * Does not assume the input is sorted.
 */
export function findLastPaymentDate(payments: Payment[]): string | undefined {
  if (payments.length === 0) return undefined;
  return payments.reduce((latest, payment) =>
    new Date(payment.paidAt).getTime() > new Date(latest.paidAt).getTime() ? payment : latest
  ).paidAt;
}
