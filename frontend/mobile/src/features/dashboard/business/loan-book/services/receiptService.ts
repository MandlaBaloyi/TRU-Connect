/**
 * Loan Book — receipt content assembly. PURE (no capture, no sharing —
 * see hooks/useShareReceipt.ts for that).
 *
 * VERIFICATION MODEL: this receipt is NOT a cryptographically signed
 * legal document — consistent with Doc 06 §12.3 ("TRUConnect does not
 * lend, collect, or adjudicate disputes"). If a dispute arises, the only
 * party who can actually verify anything is the business owner, since
 * they're the one with the live record in the app. The reference code
 * below exists so that verification is possible at all: short enough to
 * read aloud over a phone call, unique enough to find the right entry.
 *
 * FUTURE BUSINESS PROFILE: `businessName` is accepted as an explicit
 * optional parameter rather than looked up here, specifically so that
 * once a Business Profile feature exists, the caller can pass a real
 * business name straight through with ZERO changes to this file — only
 * the caller (LoanDetailsScreen) needs to change where it sources the
 * value from.
 */

import type { Customer, LoanEntryView } from "../types";
import { formatCents } from "./loanMapper";
import { formatAge } from "../algorithms/agingCalculator";

export interface ReceiptData {
  referenceCode: string;
  customerName: string;
  /** "Thandi's shop" today; a real registered business name once
   *  Business Profile exists. Never fabricated here — always supplied. */
  fromLabel: string;
  saleDateLabel: string;
  description?: string;
  originalAmountLabel: string;
  amountPaidLabel: string;
  outstandingAmountLabel: string;
  status: LoanEntryView["status"];
  isPartlyPaid: boolean;
  generatedAtLabel: string;
}

/**
 * Short, speakable reference derived from the entry's own id — not a
 * separate stored value, so it never drifts out of sync with the entry
 * it points to. Six characters keeps it readable aloud over a phone call
 * ("L B four six two nine seven") while still being specific enough,
 * combined with the customer's name, to find the right entry quickly.
 */
export function generateReferenceCode(entryId: string): string {
  const alnum = entryId.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();
  const tail = alnum.slice(-6).padStart(6, "0");
  return `LB-${tail}`;
}

/**
 * `fromLabel` construction: "{FirstName}'s shop" today, using the
 * logged-in business owner's name. Falls back to a generic label if a
 * name genuinely isn't available (should be rare — registration
 * requires a first name), rather than showing an empty "'s shop".
 */
export function buildFromLabel(ownerFirstName?: string): string {
  const trimmed = ownerFirstName?.trim();
  if (!trimmed) return "Sent via TruConnect";
  return `${trimmed}'s shop`;
}

export function buildReceiptData(
  loan: LoanEntryView,
  customer: Customer,
  ownerFirstName?: string,
  now: Date = new Date()
): ReceiptData {
  const saleDate = new Date(loan.entry.saleDate);

  return {
    referenceCode: generateReferenceCode(loan.entry.id),
    customerName: customer.name,
    fromLabel: buildFromLabel(ownerFirstName),
    saleDateLabel: saleDate.toLocaleDateString("en-ZA", {
      day: "numeric",
      month: "long",
      year: "numeric",
    }),
    description: loan.entry.description,
    originalAmountLabel: formatCents(loan.entry.originalAmount),
    amountPaidLabel: formatCents(loan.amountPaid),
    outstandingAmountLabel: formatCents(loan.outstandingAmount),
    status: loan.status,
    isPartlyPaid: loan.amountPaid > 0 && loan.outstandingAmount > 0,
    generatedAtLabel: now.toLocaleString("en-ZA", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }),
  };
}

export const RECEIPT_STATUS_LABEL: Record<LoanEntryView["status"], string> = {
  OUTSTANDING: "Unpaid",
  OVERDUE: "Overdue",
  PAID: "Paid in full",
};
