/**
 * Loan Book — internal risk signal. PURE.
 * Ref: docs/07_DATA_AND_TRUST_ENGINE.txt, docs/04_DATABASE_DESIGN.txt §6
 *
 * ============================================================
 *  DO NOT RENDER ANYTHING FROM THIS FILE IN THE UI.
 * ============================================================
 *
 * This computes a numeric risk signal about a PRIVATE INDIVIDUAL who
 * never signed up for TRU Connect — a shop's neighbour, recorded in
 * someone else's credit book. That is a materially different thing from
 * scoring a consenting platform user.
 *
 * Doc 04 §6: these scores "are not credit scores and must never be
 * presented as such."
 *
 * Concretely, the following must never appear on a screen next to a
 * customer's name:
 *      "High Risk"  /  "Medium Risk"  /  "Low Risk"
 *      a 0–100 score, a star rating, a red/amber/green person badge
 *
 * What the shop owner sees instead comes from
 * repaymentPredictor.describeRepaymentBehaviour() — factual statements
 * ("Settled 8 of 9 purchases") they can verify against their own memory,
 * rather than a judgement the app has formed about a person.
 *
 * WHY COMPUTE IT AT ALL: TruePoint's lending infrastructure will
 * eventually consume aggregate behavioural signal (Doc 07). Doc 06 §15
 * lists "Loan Book settlement patterns (aggregate behaviour only)" as a
 * trust recalculation trigger. The signal has real downstream value —
 * it just has no business being a label on someone's face today.
 *
 * If a future requirement genuinely needs this surfaced, that is a
 * product and legal decision (POPIA, consent, the fact that the data
 * subject is not a user), not a UI tweak. It should not happen because
 * a screen looked sparse.
 */

import type { InternalBehaviouralSignal, LoanEntry, Payment } from "../types";
import { calculateOutstanding } from "./balanceCalculator";
import { calculateDaysOverdue, DEFAULT_OVERDUE_THRESHOLD_DAYS } from "./agingCalculator";

interface EntryWithPayments {
  entry: LoanEntry;
  payments: Payment[];
}

/**
 * INTERNAL ONLY. Aggregate exposure and overdue concentration for one
 * customer, for eventual TruePoint consumption.
 *
 * Returns raw components rather than a single grade, deliberately: a
 * single number invites a label, whereas components invite analysis.
 */
export interface InternalRiskComponents {
  customerId: string;
  /** Total still owed across all entries, in cents. */
  totalExposure: number;
  /** Share of open entries that are overdue, 0–1. */
  overdueRatio: number;
  /** Days overdue on the oldest overdue entry; 0 if none. */
  worstDaysOverdue: number;
  /** Count of entries never settled and now overdue. */
  overdueEntryCount: number;
  calculatedAt: string;
}

export function computeInternalRiskComponents(
  customerId: string,
  pairs: EntryWithPayments[],
  thresholdDays: number = DEFAULT_OVERDUE_THRESHOLD_DAYS,
  now: Date = new Date()
): InternalRiskComponents {
  const openPairs = pairs.filter(
    ({ entry, payments }) => calculateOutstanding(entry, payments) > 0
  );

  const totalExposure = openPairs.reduce(
    (total, { entry, payments }) => total + calculateOutstanding(entry, payments),
    0
  );

  const overdueDays = openPairs.map(({ entry, payments }) =>
    calculateDaysOverdue(entry, payments, thresholdDays, now)
  );

  const overdueEntryCount = overdueDays.filter((days) => days > 0).length;

  return {
    customerId,
    totalExposure,
    overdueRatio: openPairs.length > 0 ? overdueEntryCount / openPairs.length : 0,
    worstDaysOverdue: overdueDays.length > 0 ? Math.max(...overdueDays) : 0,
    overdueEntryCount,
    calculatedAt: now.toISOString(),
  };
}

/**
 * INTERNAL ONLY. Combines the repayment signal with exposure into a
 * single 0–100 value for downstream systems.
 *
 * Named `...ForInternalUse` rather than `getRiskScore` on purpose: the
 * name should make an inappropriate import obvious in a diff.
 */
export function computeRiskSignalForInternalUse(
  repayment: InternalBehaviouralSignal,
  risk: InternalRiskComponents
): number {
  // Reliability contributes positively; overdue concentration negatively.
  const reliabilityComponent = repayment.repaymentReliability * 0.6;
  const overduePenalty = risk.overdueRatio * 40;
  return Math.max(0, Math.min(100, Math.round(reliabilityComponent + (40 - overduePenalty))));
}

/**
 * The ONLY thing from this file that may influence the UI — and even
 * then, indirectly and about a DEBT, never about a PERSON.
 *
 * "This debt is 45 days overdue" is a fact about a transaction.
 * "This customer is high risk" is a judgement about a human being.
 * The first is fine to show; the second is what this file exists to keep
 * out of the interface.
 */
export function describeOverdueFact(
  entry: LoanEntry,
  payments: Payment[],
  thresholdDays: number = DEFAULT_OVERDUE_THRESHOLD_DAYS,
  now: Date = new Date()
): string | null {
  const daysOverdue = calculateDaysOverdue(entry, payments, thresholdDays, now);
  if (daysOverdue === 0) return null;
  if (daysOverdue === 1) return "1 day overdue";
  if (daysOverdue < 30) return `${daysOverdue} days overdue`;
  const months = Math.floor(daysOverdue / 30);
  return months === 1 ? "Over a month overdue" : `Over ${months} months overdue`;
}
