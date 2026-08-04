/**
 * Loan Book — repayment behaviour prediction. PURE.
 * Ref: docs/07_DATA_AND_TRUST_ENGINE.txt, docs/04_DATABASE_DESIGN.txt §6
 *
 * TWO OUTPUTS, DELIBERATELY SEPARATED:
 *
 *   predictRepaymentBehaviour()  -> InternalBehaviouralSignal
 *        Numeric. Feeds TruePoint's eventual behavioural intelligence.
 *        NEVER rendered.
 *
 *   describeRepaymentBehaviour() -> BehaviouralInsight[]
 *        Plain factual statements a shop owner can verify against their
 *        own memory: "Usually pays within 8 days."
 *        This is the ONLY output any screen may use.
 *
 * The separation is the point. A number like 0.42 becomes a label like
 * "Medium Risk" the moment someone decides the screen looks empty — and
 * that label sits next to a named private individual who never signed up
 * for anything. Doc 04 §6 is explicit that these scores "are not credit
 * scores and must never be presented as such." Two return types with two
 * docstrings makes that boundary something a future reader has to
 * deliberately cross, rather than something they wander across.
 *
 * HONESTY ABOUT SMALL SAMPLES: every function here refuses to predict
 * from thin history. Two payments is not a pattern. Returning null and
 * saying nothing is better than manufacturing confidence — a wrong
 * "usually pays within 5 days" would have the owner extending credit on
 * a fiction.
 */

import type {
  BehaviouralInsight,
  Customer,
  InternalBehaviouralSignal,
  LoanEntry,
  Payment,
} from "../types";
import { calculateOutstanding, findLastPaymentDate } from "./balanceCalculator";
import { daysSince } from "./agingCalculator";

/** Below this many settled entries, we decline to predict. */
const MIN_SAMPLE_FOR_PREDICTION = 3;

interface EntryWithPayments {
  entry: LoanEntry;
  payments: Payment[];
}

/**
 * Days each settled entry took from sale to full settlement.
 * Unsettled entries are excluded — they have no completion time yet, and
 * including them as "so far" would bias the average downward.
 */
export function calculateSettlementDurations(pairs: EntryWithPayments[]): number[] {
  return pairs
    .filter(({ entry, payments }) => calculateOutstanding(entry, payments) === 0)
    .map(({ entry, payments }) => {
      const settledAt = entry.settledAt ?? findLastPaymentDate(payments);
      if (!settledAt) return null;
      return daysSince(entry.saleDate, new Date(settledAt));
    })
    .filter((days): days is number => days !== null);
}

/**
 * Median, not mean.
 *
 * One customer who took 400 days to settle a single debt would drag a
 * mean far away from what actually typically happens. The median answers
 * "what usually happens", which is the honest claim to put in front of
 * someone.
 */
export function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? Math.round((sorted[mid - 1] + sorted[mid]) / 2) : sorted[mid];
}

/**
 * INTERNAL ONLY — never render this.
 * Numeric behavioural signal for TruePoint (Doc 07).
 */
export function predictRepaymentBehaviour(
  customer: Customer,
  pairs: EntryWithPayments[],
  now: Date = new Date()
): InternalBehaviouralSignal {
  const durations = calculateSettlementDurations(pairs);
  const settledCount = durations.length;
  const totalCount = pairs.length;

  const predictedDaysToSettle =
    settledCount >= MIN_SAMPLE_FOR_PREDICTION ? median(durations) : null;

  // Reliability blends "how many did they finish" with "how promptly".
  // Both matter: someone who settles everything slowly is different from
  // someone who settles half of it quickly.
  const settlementRate = totalCount > 0 ? settledCount / totalCount : 0;
  const promptness =
    predictedDaysToSettle === null ? 0.5 : Math.max(0, 1 - predictedDaysToSettle / 90);

  const repaymentReliability =
    settledCount >= MIN_SAMPLE_FOR_PREDICTION
      ? Math.round((settlementRate * 0.6 + promptness * 0.4) * 100)
      : Math.round(settlementRate * 100);

  return {
    customerId: customer.id,
    repaymentReliability,
    predictedDaysToSettle,
    sampleSize: settledCount,
    calculatedAt: now.toISOString(),
  };
}

/**
 * SAFE TO RENDER — factual statements only.
 *
 * Every string below describes something that demonstrably happened and
 * that the owner could confirm from their own records. None of them
 * grade the person.
 */
export function describeRepaymentBehaviour(
  pairs: EntryWithPayments[],
  now: Date = new Date()
): BehaviouralInsight[] {
  const insights: BehaviouralInsight[] = [];
  const allPayments = pairs.flatMap(({ payments }) => payments);

  // --- Last payment -------------------------------------------------
  const lastPaymentAt = findLastPaymentDate(allPayments);
  if (lastPaymentAt) {
    const days = daysSince(lastPaymentAt, now);
    insights.push({
      kind: "LAST_PAYMENT",
      statement:
        days === 0
          ? "Paid today"
          : days === 1
            ? "Paid yesterday"
            : `Last paid ${days} days ago`,
      tone: days <= 14 ? "POSITIVE" : days <= 45 ? "NEUTRAL" : "ATTENTION",
    });
  }

  // --- Typical settlement time --------------------------------------
  const durations = calculateSettlementDurations(pairs);
  if (durations.length >= MIN_SAMPLE_FOR_PREDICTION) {
    const typical = median(durations);
    if (typical !== null) {
      insights.push({
        kind: "AVERAGE_REPAYMENT_DAYS",
        statement:
          typical <= 1 ? "Usually pays the same day" : `Usually pays within ${typical} days`,
        tone: typical <= 14 ? "POSITIVE" : typical <= 30 ? "NEUTRAL" : "ATTENTION",
      });
    }
  }

  // --- Settlement consistency ---------------------------------------
  // Only stated once there's enough history for the ratio to mean
  // something. "1 of 1 settled" is not information.
  const settledCount = durations.length;
  const totalCount = pairs.length;
  if (totalCount >= MIN_SAMPLE_FOR_PREDICTION) {
    insights.push({
      kind: "SETTLEMENT_CONSISTENCY",
      statement: `Settled ${settledCount} of ${totalCount} purchases`,
      tone:
        settledCount === totalCount
          ? "POSITIVE"
          : settledCount / totalCount >= 0.5
            ? "NEUTRAL"
            : "ATTENTION",
    });
  }

  // --- Outstanding trend --------------------------------------------
  const openCount = pairs.filter(
    ({ entry, payments }) => calculateOutstanding(entry, payments) > 0
  ).length;
  if (openCount >= 3) {
    insights.push({
      kind: "OUTSTANDING_TREND",
      statement: `${openCount} purchases still unpaid`,
      tone: "ATTENTION",
    });
  }

  return insights;
}

/**
 * Purchase frequency — "Buys about every 7 days".
 *
 * Separate from the above because it describes buying, not repaying, and
 * a business may want it in a different place on the screen.
 */
export function describePurchaseFrequency(
  entries: LoanEntry[],
  now: Date = new Date()
): BehaviouralInsight | null {
  if (entries.length < MIN_SAMPLE_FOR_PREDICTION) return null;

  const dates = entries
    .map((entry) => new Date(entry.saleDate).getTime())
    .sort((a, b) => a - b);

  const gaps: number[] = [];
  for (let i = 1; i < dates.length; i++) {
    gaps.push(Math.round((dates[i] - dates[i - 1]) / (24 * 60 * 60 * 1000)));
  }

  const typicalGap = median(gaps);
  if (typicalGap === null || typicalGap === 0) return null;

  return {
    kind: "PURCHASE_FREQUENCY",
    statement:
      typicalGap <= 2
        ? "Buys almost every day"
        : typicalGap <= 9
          ? "Buys about every week"
          : typicalGap <= 20
            ? "Buys about every two weeks"
            : "Buys about once a month",
    tone: "NEUTRAL",
  };
}
