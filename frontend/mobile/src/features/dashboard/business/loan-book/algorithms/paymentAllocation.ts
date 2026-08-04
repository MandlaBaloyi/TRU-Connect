/**
 * Loan Book — payment allocation and validation. PURE.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt §12.2, §12.3
 *
 * Doc 06 §12.3 gives two hard rules:
 *   "Repayments may exceed neither the outstanding amount nor be negative."
 *   "Partial repayment is fully supported."
 *
 * This file is where those are enforced, as pure functions, so the same
 * rules apply identically whether a payment arrives from the Record
 * Payment screen, a future bulk import, or (later) a sync replay. Rules
 * enforced only in a screen are rules that stop existing the moment a
 * second code path appears.
 */

import type { Cents, LoanEntry, Payment } from "../types";
import { calculateOutstanding } from "./balanceCalculator";

export type PaymentRejectionReason =
  | "AMOUNT_NOT_POSITIVE"
  | "AMOUNT_EXCEEDS_OUTSTANDING"
  | "ENTRY_ALREADY_SETTLED"
  | "AMOUNT_NOT_WHOLE_CENTS";

export interface PaymentValidationResult {
  isValid: boolean;
  reason?: PaymentRejectionReason;
  /** Plain-language message safe to show directly (Doc 02 §14). */
  message?: string;
  /** What the balance WOULD become — lets the screen preview the result
   *  before the owner commits, rather than only reporting afterwards. */
  resultingOutstanding?: Cents;
}

/**
 * Validate a proposed payment against an entry's real, derived balance.
 *
 * Returns a result object rather than throwing: an invalid amount is an
 * ordinary thing a person does while typing, not an exceptional
 * condition. Doc 02 §9 wants inline validation beneath the field, which
 * needs a value to render, not an exception to catch.
 */
export function validatePayment(
  entry: LoanEntry,
  existingPayments: Payment[],
  amount: Cents
): PaymentValidationResult {
  const outstanding = calculateOutstanding(entry, existingPayments);

  if (!Number.isInteger(amount)) {
    return {
      isValid: false,
      reason: "AMOUNT_NOT_WHOLE_CENTS",
      message: "Enter a valid amount.",
    };
  }

  if (amount <= 0) {
    return {
      isValid: false,
      reason: "AMOUNT_NOT_POSITIVE",
      message: "Enter an amount greater than zero.",
    };
  }

  if (outstanding === 0) {
    return {
      isValid: false,
      reason: "ENTRY_ALREADY_SETTLED",
      message: "This is already fully paid.",
    };
  }

  if (amount > outstanding) {
    return {
      isValid: false,
      reason: "AMOUNT_EXCEEDS_OUTSTANDING",
      message: `That's more than the ${formatCentsForMessage(outstanding)} still owed.`,
      resultingOutstanding: 0,
    };
  }

  return {
    isValid: true,
    resultingOutstanding: outstanding - amount,
  };
}

/**
 * Whether this payment settles the entry completely — drives the
 * "settled" celebration and the is_settled/settled_at write.
 */
export function willSettleEntry(
  entry: LoanEntry,
  existingPayments: Payment[],
  amount: Cents
): boolean {
  return calculateOutstanding(entry, existingPayments) - amount <= 0;
}

/**
 * Suggested quick-amount buttons for the Record Payment screen.
 *
 * Doc 02 §1.2 ("Minimum Typing") and the ≤15s target mean the common
 * cases should be one tap, not a typed amount. Returns the full
 * outstanding plus round-number partials below it, deduplicated and
 * always ascending.
 *
 * Round numbers matter because informal payments are made in cash — a
 * customer hands over a R50 or R100 note, not R47.30.
 */
export function suggestQuickAmounts(outstanding: Cents): Cents[] {
  if (outstanding <= 0) return [];

  const ROUND_STEPS: Cents[] = [
    5000, // R50
    10000, // R100
    20000, // R200
    50000, // R500
  ];

  const suggestions = ROUND_STEPS.filter((step) => step < outstanding);
  suggestions.push(outstanding); // "Pay it all off" — always offered last

  return Array.from(new Set(suggestions)).sort((a, b) => a - b);
}

/**
 * Allocate a payment across several entries for one customer,
 * oldest-first.
 *
 * NOT used by Phase 1 screens (payments are recorded against one chosen
 * entry, which keeps the flow to a single tap). It exists because
 * "customer hands over R200 against three open debts" is how informal
 * repayment actually happens, and oldest-first is the fair, conventional
 * ordering. Kept pure and tested so the eventual "pay across all"
 * feature is a UI addition rather than new logic.
 */
export function allocateAcrossEntries(
  pairs: { entry: LoanEntry; payments: Payment[] }[],
  amount: Cents
): { entryId: string; allocated: Cents }[] {
  const openPairs = pairs
    .filter(({ entry, payments }) => calculateOutstanding(entry, payments) > 0)
    .sort(
      (a, b) => new Date(a.entry.saleDate).getTime() - new Date(b.entry.saleDate).getTime()
    );

  const allocations: { entryId: string; allocated: Cents }[] = [];
  let remaining = amount;

  for (const { entry, payments } of openPairs) {
    if (remaining <= 0) break;
    const outstanding = calculateOutstanding(entry, payments);
    const allocated = Math.min(outstanding, remaining);
    allocations.push({ entryId: entry.id, allocated });
    remaining -= allocated;
  }

  return allocations;
}

/** Minimal formatter used only inside validation messages. Display
 *  formatting proper lives in the presentation layer. */
function formatCentsForMessage(cents: Cents): string {
  return `R ${(cents / 100).toFixed(2)}`;
}
